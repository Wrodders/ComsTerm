import json
from dataclasses import dataclass, field, asdict
from typing import List, Union

from common.messages import TopicMap

@dataclass
class CfgBase():
    def save(self, cfgFile: str):
        raise NotImplementedError
    
    def populate(self, cfg_data: dict):
        raise NotImplementedError
    
    def load(self, cfgFile: str):
        with open(cfgFile, 'r') as f:
            cfg_data = json.load(f)
            self.populate(cfg_data)

@dataclass
class SinkCfg():
    protocol: tuple[str, ...] = field(default_factory=tuple)
    name: str = "Sink 0"
    sampleBufferLen: int = 100

""" ----------------- Plot App Config ----------------- """
@dataclass
class LinePlotCfg():
    yrange: tuple[float, float] = (-100, 100)

@dataclass
class ScatterPlotCfg():
    yrange: tuple[float, float] = (-100, 100)
    xrange: tuple[float, float] = (-100, 100)
    marker: str = "o"

@dataclass
class BarPlotCfg():
    ylim: int = 100
    barWidth: float = 0.35

PlotTypeMap = {
            "LINE": LinePlotCfg,
            "SCATTER": ScatterPlotCfg,
            "BAR": BarPlotCfg
        }
@dataclass
class PlotCfg(SinkCfg):
    plotType: str = "LINE"
    typeCfg: Union[LinePlotCfg, ScatterPlotCfg, BarPlotCfg] = field(default_factory=LinePlotCfg)
    maxPlotSeries: int = 8

@dataclass
class PlotAppCfg(CfgBase):
    plotConfigs : List[PlotCfg] = field(default_factory=lambda: [PlotCfg()])
    maxPlots: int = 4

    def save(self, cfgFilePath: str):
        with open(cfgFilePath, "w") as file:
            json.dump(asdict(self), file,indent=4)

    def populate(self, cfg_data: dict):
        self.plotConfigs = list()
        for cfg in cfg_data["plotConfigs"]:
            if(cfg.get("plotName") in [cfg.name for cfg in self.plotConfigs]):
                continue # Skip duplicate plot names
            cfg["typeCfg"] = PlotTypeMap[cfg["plotType"]](**cfg["typeCfg"])
            self.plotConfigs.append(PlotCfg(**cfg)) # unpack dict to PlotCfg
        self.maxPlots = cfg_data["maxPlots"]

""" ----------------- Console App Config ----------------- """
@dataclass
class ConsoleCfg(SinkCfg):
    name: str = "Console 0"

@dataclass
class ConsoleAppCfg(CfgBase):
    consoleCfgs : list[ConsoleCfg] = field(default_factory=lambda: [ConsoleCfg()])
    maxNumConsoles : int = 4

    def save(self, cfgFile: str):
        with open(cfgFile, 'w') as f:
            json.dump(asdict(self), f, indent=4)
    
    def populate(self, cfg_data: dict):
        self.maxNumConsoles = cfg_data["maxNumConsoles"]
        for consoleCfg in cfg_data["consoleCfgs"]:
            if(consoleCfg.get("name") in [cfg.name for cfg in self.consoleCfgs]):
                continue # Skip duplicate console names
            self.consoleCfgs.append(ConsoleCfg(**consoleCfg)) # unpack dict to ConsoleCfg


""" ----------------- Controls App Config ----------------- """
@dataclass
class ControllerCfg(CfgBase):
    paramRegMapFile: str = "paramRegMap.csv"

    def save(self, cfgFile: str):
        with open(cfgFile, 'w') as f:
            json.dump(asdict(self), f, indent=4)
    
    def populate(self, cfg_data: dict):
        self.paramRegMapFile = cfg_data["paramRegMapFile"]


""" ----------------- Main App Config ----------------- """

AppTypeMap = {
    "PLOT" : PlotAppCfg,
    "CONSOLE" : ConsoleAppCfg,
    "CONTROL" : ControllerCfg
}
@dataclass
class AppCfg():
    appType : str = "PLOT"
    typeCfg : Union[PlotAppCfg, ConsoleAppCfg, ControllerCfg] = field(default_factory=PlotAppCfg)

@dataclass
class SessionConfig(CfgBase): # Session Runtime Configuration
    appCfgs : List[AppCfg] = field(default_factory=list) # list of app configurations
    topicMap : TopicMap = field(default_factory=TopicMap)
   
    def __post_init__(self):
        self.topicMap.loadTopicsFromCSV("devicePub.csv")

    def save(self, cfgFile: str):
        with open(cfgFile, 'w') as f:
            cfg_data = {"appCfgs" : [asdict(appCfg) for appCfg in self.appCfgs]}
            json.dump(cfg_data, f, indent=4)

    def populate(self, cfg_data: dict):
        for cfg in cfg_data["appCfgs"]:
            if(cfg.get("appType") in [cfg.appType for cfg in self.appCfgs]):
                continue # Skip duplicate app types
            appType = cfg["appType"]
            appCfgType = AppTypeMap[appType]
            self.appCfgs.append(AppCfg(appType=appType, typeCfg=appCfgType(**cfg)))