import json
from dataclasses import dataclass, field, asdict
from typing import List, Union

from common.messages import TopicMap

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
class PlotAppCfg():
    plotConfigs : List[PlotCfg] = field(default_factory=lambda: [PlotCfg()]) # Default Plot Config
    maxPlots: int = 4

    def load(self, cfgFile: str):
        with open(cfgFile, 'r') as f:
            cfg_data = json.load(f)
            self.populate(cfg_data)

    def populate(self, cfg_data: dict):
        self.plotConfigs = list() # Reset plotConfigs list
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
class ConsoleAppCfg():
    consoleCfgs : list[ConsoleCfg] = field(default_factory=lambda: [ConsoleCfg()]) # Default Console Config
    maxNumConsoles : int = 4

    def load(self, cfgFile: str):
        with open(cfgFile, 'r') as f:
            cfg_data = json.load(f)
            self.populate(cfg_data)
   
    def populate(self, cfg_data: dict):
        self.consoleCfgs = list() # Reset consoleCfgs list
        for consoleCfg in cfg_data["consoleCfgs"]:
            if(consoleCfg.get("name") in [cfg.name for cfg in self.consoleCfgs]):
                continue
            print(consoleCfg)
            self.consoleCfgs.append(ConsoleCfg(**consoleCfg)) # unpack dict to ConsoleCfg
        self.maxNumConsoles = cfg_data["maxNumConsoles"]
""" ----------------- Controls App Config ----------------- """
@dataclass
class ControllerCfg():
    paramRegMapFile: str = "paramRegMap.csv"

    def load(self, cfgFile: str):
        with open(cfgFile, 'r') as f:
            cfg_data = json.load(f)
            self.populate(cfg_data)

    def populate(self, cfg_data: dict):
        self.paramRegMapFile = cfg_data["paramRegMapFile"]


""" ----------------- Main App Config ----------------- """
AppTypeMap = {
    "PLOT" : PlotAppCfg,
    "CONSOLE" : ConsoleAppCfg,
    "CONTROL" : ControllerCfg
}

@dataclass
class SessionConfig(): # Session Runtime Configuration
    plotAppCfg : PlotAppCfg = field(default_factory=PlotAppCfg)
    consoleAppCfg : ConsoleAppCfg = field(default_factory=ConsoleAppCfg)
    controllerAppCfg : ControllerCfg = field(default_factory=ControllerCfg)
    topicMap : TopicMap = field(default_factory=TopicMap)
   
    def __post_init__(self):
        self.topicMap.loadTopicsFromCSV("devicePub.csv")

    def load(self, cfgFile: str):
        with open(cfgFile, 'r') as f:
            cfg_data = json.load(f)
            self.populate(cfg_data)

    def save(self, cfgFile: str):
        with open(cfgFile, 'w') as f:
            sessionCfg_data = {
                "plotApp": self.plotAppCfg,
                "consoleApp": self.consoleAppCfg,
                "controlsApp": self.controllerAppCfg
            }
            # Use custom encoder to serialize dataclasses properly
            json.dump(sessionCfg_data, f, indent=4, default=lambda obj: obj.__dict__)

    def populate(self, cfg_data: dict):
        self.plotAppCfg.populate(cfg_data["plotApp"])
        self.consoleAppCfg.populate(cfg_data["consoleApp"])
        self.controllerAppCfg.populate(cfg_data["controlsApp"])

        
           