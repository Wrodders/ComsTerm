import numpy as np
import matplotlib.pyplot as plt

def generate_chirp(buffer_size, min_freq, max_freq, duration_sec, sample_time):
    time_points = np.linspace(0, duration_sec, int(duration_sec / sample_time), endpoint=False)
    frequency_points = np.linspace(min_freq, max_freq, len(time_points))
    phase_offsets = 2 * np.pi * np.cumsum(frequency_points) * sample_time
    
    chirp_signal = np.sin(phase_offsets)
    
    return time_points, chirp_signal

def plot_chirp(buffer_size, min_freq, max_freq, duration_sec, sample_time):
    time_points, chirp_signal = generate_chirp(buffer_size, min_freq, max_freq, duration_sec, sample_time)
    
    plt.plot(time_points, chirp_signal)
    plt.title('Chirp Signal')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.grid(True)
    plt.show()

# Example usage
buffer_size = 1024
min_freq = 0.1  # Minimum frequency (Hz)
max_freq = 10  # Maximum frequency (Hz)
duration_sec = 5  # Duration of the signal in seconds
sample_time = 0.001  # Sample time in seconds

plot_chirp(buffer_size, min_freq, max_freq, duration_sec, sample_time)
