// Standard C++ includes
#include <fstream>
#include <random>

// Common includes
#include "../common/timer.h"
#include "../common/spike_csv_recorder.h"

// Model parameters
#include "parameters.h"

// Auto-generated model code
#include "mad_2007_CODE/definitions.h"

int main()
{
    {
        Timer<> tim("Allocation:");
        allocateMem();
    }
    {
        Timer<> tim("Initialization:");
        initialize();
    }

    // Final setup
    {
        Timer<> tim("Sparse init:");
        initmad_2007();
    }

    {
        // Open CSV output files
        SpikeCSVRecorderDelayCached spikes("spikes.csv", Parameters::numExcitatory,
                                           spkQuePtrE, glbSpkCntE, glbSpkE);
        {
            Timer<> tim("Simulation:");
            // Loop through timesteps
            double averageSpikes = 0.0;
            const double alpha = 0.001;
            while(t < Parameters::durationMs) {
                // Simulate
#ifndef CPU_ONLY
                stepTimeGPU();

                pullECurrentSpikesFromDevice();
#else
                stepTimeCPU();
#endif
                averageSpikes = (alpha * (double)spikeCount_E) + ((1.0 - alpha) * averageSpikes);
                if((iT % 1000) == 0) {

                    std::cout << (t / Parameters::durationMs) * 100.0 << "%" << std::endl;
                    std::cout << "Moving average spike rate:" << (averageSpikes / (double)Parameters::numExcitatory) / (Parameters::timestep / 1000.0) << " Hz" << std::endl;
                }

                // Record last 50s of spiking activity
                if(t > (Parameters::durationMs - (50.0 * 1000.0))) {
                    spikes.record(t);
                }
            }
        }
    }
#ifdef MEASURE_TIMING
    std::cout << "Timing:" << std::endl;
    std::cout << "\tHost init:" << initHost_tme * 1000.0 << std::endl;
    std::cout << "\tDevice init:" << initDevice_tme * 1000.0 << std::endl;
    std::cout << "\tHost sparse init:" << sparseInitHost_tme * 1000.0 << std::endl;
    std::cout << "\tDevice sparse init:" << sparseInitDevice_tme * 1000.0 << std::endl;
    std::cout << "\tNeuron simulation:" << neuron_tme * 1000.0 << std::endl;
    std::cout << "\tSynapse simulation:" << synapse_tme * 1000.0 << std::endl;
#ifndef STATIC
    std::cout << "\tPostsynaptic learning:" << learning_tme * 1000.0 << std::endl;
#endif
#endif
#ifndef STATIC
    {
        Timer<> tim("Weight analysis:");

        // Download weights
        pullEEStateFromDevice();
        
        // **HACK** Download row lengths
        extern unsigned int *d_rowLengthEE;
        CHECK_CUDA_ERRORS(cudaMemcpy(CEE.rowLength, d_rowLengthEE, Parameters::numExcitatory * sizeof(unsigned int), cudaMemcpyDeviceToHost));

        // Write row weights to file
        std::ofstream weights("weights.bin", std::ios::binary);
        for(unsigned int i = 0; i < Parameters::numExcitatory; i++) {
            weights.write(reinterpret_cast<char*>(&gEE[i * CEE.maxRowLength]), sizeof(scalar) * CEE.rowLength[i]);
        }
    }
#endif // !STATIC
    return 0;
}
