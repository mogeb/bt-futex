import babeltrace.reader
import sys
from pprint import pprint
import numpy as np

per_cpu_holder = []
results = {}
total_events = 0
metrics = ['perf_thread_cache_misses', 'perf_thread_instructions', 'perf_thread_L1_dcache_load_misses', 'perf_thread_dTLB_load_misses']
traces = ['/home/mogeb/tmp/pmu-bufferlist/bufferlist_append/vector/uid/1000/64-bit/',
    '/home/mogeb/tmp/pmu-bufferlist/bufferlist_append/list/uid/1000/64-bit/']


def usage():
    print('Usage: ' + sys.argv[0] + ' TRACE')


def compile_scatter_plot(args):
    global metrics

    fontP = FontProperties()
    fontP.set_size('small')

    for metric in metrics:
        plt.subplot(2, 2, i)
        for trace in traces:
            metric = metric.strip()
            plt.scatter(values[trace][metric], values[trace]['latency'], color=tracers_colors[trace],
                        alpha=0.3, label=trace)
        plt.title('Latency according to ' + metric)
        plt.xlabel(metric)
        plt.ylabel('Latency in ns')
        # plt.legend(prop=fontP)
        i += 1
    # plt.legend(bbox_to_anchor=(1, 0), loc=1, borderaxespad=0.)
    plt.legend(loc=4, borderaxespad=0., fontsize='small')
    plt.show()


def count_pmu(trace):
    global per_cpu_holder
    global results
    global total_events
    global metrics
    i = 0

    trace_collection = babeltrace.reader.TraceCollection()
    trace_collection.add_trace(trace, 'ctf')

    print('duration', end='')
    for metric in metrics:
        print(',' + metric, end='')
    print('\n')

    for event in trace_collection.events:
        if i >= 4000:
            break
        i = i + 1
        cpu = event['cpu_id']

        if event.name == 'analyze:bufferlist_append_begin':
            while cpu >= len(per_cpu_holder):
                per_cpu_holder.append({})

            for metric in metrics:
                if metric not in per_cpu_holder[cpu]:
                    per_cpu_holder[cpu][metric] = -1

                per_cpu_holder[cpu][metric] = event[metric]

            per_cpu_holder[cpu]['time'] = event.timestamp

        if event.name == 'analyze:bufferlist_append_end':
            if 'time' not in results:
                results['time'] = 0
            if cpu >= len(per_cpu_holder):
                continue
            duration = event.timestamp - per_cpu_holder[cpu]['time']

            results['time'] = results['time'] + duration
            total_events = total_events + 1

            print('{}'.format(duration), end='')

            for metric in metrics:
                print(',', end='')
                metric_value = event[metric]
                metric_value_begin = per_cpu_holder[cpu][metric]

                if metric not in results:
                    results[metric] = 0

                results[metric] = results[metric] + metric_value - metric_value_begin
                print(metric_value - metric_value_begin, end='')
                # print(metric_value - metric_value_begin)
            print('')

    print('')
    pprint(results)
    print('\ntime = ', end='')
    print(results['time'] / total_events)
    for metric in metrics:
        print(metric + ": ", end='')
        print(results[metric] / total_events)


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        usage()
        exit()
    count_pmu(sys.argv[1])
