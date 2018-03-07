import babeltrace.reader
import sys
from pprint import pprint
import matplotlib
matplotlib.use('GTK3Agg')
import pylab
from pylab import *
import numpy as np
from matplotlib.font_manager import FontProperties
from collections import defaultdict

per_cpu_holder = []
results = {}
total_events = 0
metrics = ['perf_thread_cache_misses', 'perf_thread_instructions', 'perf_thread_L1_dcache_load_misses',
           'perf_thread_branch_misses', 'perf_thread_dTLB_load_misses']
legend = ['latency', 'perf_thread_cache_misses', 'perf_thread_instructions',
          'perf_thread_L1_dcache_load_misses', 'perf_thread_dTLB_load_misses', 'perf_thread_branch_misses']
traces = ['/home/mogeb/tmp/pmu-bufferlist/new_bufferlist_append/list/uid/1000/64-bit/',
          '/home/mogeb/tmp/pmu-bufferlist/new_bufferlist_append/vector/uid/1000/64-bit/']
colors = {'/home/mogeb/tmp/pmu-bufferlist/new_bufferlist_append/vector/uid/1000/64-bit/' : 'red',
          '/home/mogeb/tmp/pmu-bufferlist/new_bufferlist_append/list/uid/1000/64-bit/': 'green'}
names = {'/home/mogeb/tmp/pmu-bufferlist/new_bufferlist_append/vector/uid/1000/64-bit/' : 'vector',
         '/home/mogeb/tmp/pmu-bufferlist/new_bufferlist_append/list/uid/1000/64-bit/': 'list'}
final_results = {}


def usage():
    print('Usage: ' + sys.argv[0] + ' TRACE')


def compile_scatter_plot(args):
    global legend
    global final_results
    values = defaultdict(list)

    fontP = FontProperties()
    fontP.set_size('small')

    for trace in traces:
        fname = '/tmp/out_' + names[trace]
        values[trace] = np.genfromtxt(fname, delimiter=',', skip_header=2, names=legend, dtype=None)

    i = 0
    for metric in legend:
        if metric == 'latency':
            continue
        plt.subplot(2, 3, i)
        for trace in traces:
            plt.scatter(values[trace][metric], values[trace]['latency'], color=colors[trace],
                        alpha=0.1, label=names[trace])
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
    global final_results
    i = 0

    trace_collection = babeltrace.reader.TraceCollection()
    trace_collection.add_trace(trace, 'ctf')

    if trace not in final_results:
        final_results[trace] = []

    f = open('/tmp/out_' + names[trace], 'w+')
    f.write('latency')
    for metric in metrics:
        f.write(',' + metric)
    f.write('\n')
    print('duration', end='')
    for metric in metrics:
        print(',' + metric, end='')
    print('\n')

    for event in trace_collection.events:
        i = i + 1
        # if i <= 200:
            # continue
        if i >= 2000:
            break
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
            if 'time' not in per_cpu_holder[cpu]:
                continue
            duration = event.timestamp - per_cpu_holder[cpu]['time']

            results['time'] = results['time'] + duration
            total_events = total_events + 1

            these_results = []
            these_results.append(duration)
            f.write(str(duration))
            for metric in metrics:
                metric_value = event[metric]
                metric_value_begin = per_cpu_holder[cpu][metric]

                if metric not in results:
                    results[metric] = 0

                results[metric] = results[metric] + metric_value - metric_value_begin
                these_results.append(metric_value - metric_value_begin)
                f.write(',')
                f.write(str(metric_value - metric_value_begin))
            f.write('\n')
            final_results[trace].append(these_results)

    print('parsed ' + str(len(final_results[traces[0]])) + ' events')
    print('')
    print(names[trace])
    pprint(results)
    print('\ntime = ', end='')
    print(results['time'] / total_events)
    for metric in metrics:
        print(metric + ": ", end='')
        print(results[metric] / total_events)

    f.close()


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        usage()
        exit()
    for trace in traces:
        count_pmu(trace)
    compile_scatter_plot(final_results)
