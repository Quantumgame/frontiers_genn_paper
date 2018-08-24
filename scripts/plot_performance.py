import numpy as np
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import plot_settings
import utils

def plot(data, filename, num_ref, real_time_s=None):
    columns = zip(*data)
    device = np.asarray(columns[0],  dtype=str)

    total_sim_time = np.asarray(columns[1],  dtype=float) / 1000.0
    neuron_sim_time = np.asarray(columns[2],  dtype=float) / 1000.0
    synapse_sim_time = np.asarray(columns[3],  dtype=float) / 1000.0

    post_learn_sim_time = None if (len(columns) < 5) else np.asarray(columns[4],  dtype=float) / 1000.0

    overhead = total_sim_time - neuron_sim_time - synapse_sim_time
    if post_learn_sim_time is not None:
        overhead -= post_learn_sim_time

    fig, axis = plt.subplots(figsize=(plot_settings.column_width, 90.0 * plot_settings.mm_to_inches),
                            frameon=False)

    # Correctly place bars
    bar_width = 0.8
    bar_pad = 0.4
    bar_x = np.arange(0.0, len(device) * (bar_width + bar_pad), bar_width + bar_pad)

    offset = np.zeros(len(bar_x) - num_ref)

    # Plot stacked, GPU bars
    gpu_bar_x_slice = np.s_[:] if num_ref == 0 else np.s_[:-num_ref]

    neuron_sim_actor = axis.bar(bar_x[gpu_bar_x_slice], neuron_sim_time[gpu_bar_x_slice], bar_width)[0]
    offset += neuron_sim_time[gpu_bar_x_slice]
    synapse_sim_actor = axis.bar(bar_x[gpu_bar_x_slice], synapse_sim_time[gpu_bar_x_slice], bar_width, offset)[0]
    offset += synapse_sim_time[gpu_bar_x_slice]

    if post_learn_sim_time is not None:
        post_learn_sim_actor = axis.bar(bar_x[gpu_bar_x_slice], post_learn_sim_time[gpu_bar_x_slice], bar_width, offset)[0]
        offset += post_learn_sim_time[gpu_bar_x_slice]

    overhead_actor = axis.bar(bar_x[gpu_bar_x_slice], overhead[gpu_bar_x_slice], bar_width, offset)
    offset += overhead[gpu_bar_x_slice]

    # Plot individual other bars
    if num_ref > 0:
        axis.bar(bar_x[-num_ref:], total_sim_time[-num_ref:], bar_width, 0.0)

    # Add real-timeness annoation
    #for t, x in zip(total_sim_time, bar_x):
    #    axis.text(x, t,
    #              "%.2f$\\times$\nreal-time" % (1.0 / t),
    #              ha="center", va="bottom", )

    axis.set_ylabel("Time [s]")

    # Add legend
    axis.legend(loc="upper right", ncol=3)

    # Add realtime line
    if real_time_s is not None:
        axis.axhline(real_time_s, color="black", linestyle="--")

    # Remove vertical grid
    axis.xaxis.grid(False)

    # Add x ticks labelling delay type
    axis.set_xticks(bar_x)
    axis.set_xticklabels(device, rotation="vertical", ha="center", multialignment="right")

    if post_learn_sim_time is not None:
        fig.legend([neuron_sim_actor, synapse_sim_actor, post_learn_sim_actor, overhead_actor],
                ["Neuron simulation", "Synapse simulation", "Postsynaptic learning", "Overhead"],
                ncol=2, loc="lower center")
    else:
        fig.legend([neuron_sim_actor, synapse_sim_actor, overhead_actor],
                ["Neuron simulation", "Synapse\nsimulation", "Overhead"],
                ncol=2, loc="lower center")

    # Set tight layour - tweaking bottom to fit in axis
    # text and right to fit in right break marker
    fig.tight_layout(pad=0, rect=(0.0, 0.15, 1.0, 0.96))
    fig.savefig(filename)

# Total simulation time, neuron simulation, synapse simulation
microcircuit_data = [("Jetson TX2", 258350, 99570.4, 155284),
                     ("GeForce 1050ti", 137592, 20192.6, 21310.1),
                     ("Tesla K40c", 41911.5, 13636.2, 12431.8),
                     ("Tesla V100", 21645.4, 3215.88, 3927.9),
                     ("HPC\n(fastest)", 24296.0, 0.0, 0.0),
                     ("SpiNNaker", 200000, 0.0, 0.0)]

# Total simulation time, neuron simulation, synapse simulation, postsynaptic learning
stdp_data = [("Tesla K40m\nBitmask", 4736610, 435387, 296357, 3925070),
             ("Tesla V100\nBitmask", 564826, 100144, 82951.6, 307273),
             ("Tesla V100\nRagged", 567267, 99346.3, 85975.4, 307433)]

plot(microcircuit_data, "../figures/microcircuit_performance.eps", 2, 10.0)
plot(stdp_data, "../figures/stdp_performance.eps", 0, 200.0)
plt.show()