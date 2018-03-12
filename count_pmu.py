import babeltrace.reader
import sys
import argparse
from pprint import pprint
from collections import defaultdict

#order is important here
import matplotlib
matplotlib.use('GTK3Agg')
import pylab
from pylab import *
import numpy as np
from matplotlib.font_manager import FontProperties


per_cpu_holder = []
results = {}
total_events = 0
metrics = ['perf_thread_cache_misses', 'perf_thread_instructions', 'perf_thread_L1_dcache_load_misses',
           'perf_thread_dTLB_load_misses']
legend = ['latency', 'perf_thread_cache_misses', 'perf_thread_instructions',
          'perf_thread_L1_dcache_load_misses', 'perf_thread_dTLB_load_misses']

colors = {}
names = {}
final_results = {}
buffersize = 0
x_min = {
    'perf_thread_cache_misses': -10,
    'perf_thread_instructions': 0,
    'perf_thread_L1_dcache_load_misses': -10,
    'perf_thread_dTLB_load_misses': -5
    }
x_max = {
    'perf_thread_cache_misses': 40,
    'perf_thread_instructions': 10000,
    'perf_thread_L1_dcache_load_misses': 220,
    'perf_thread_dTLB_load_misses': 20
    }


def sizeof_fmt(num, suffix='B'):
    num = int(num)
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def usage():
    print('Usage: ' + sys.argv[0] + ' TRACE')


def compile_scatter_plot(args):
    global legend
    global final_results
    global buffersize
    global x_max
    values = defaultdict(list)

    fontP = FontProperties()
    fontP.set_size('small')

    for trace in traces:
        fname = '/tmp/out_' + names[trace]
        values[trace] = np.genfromtxt(fname, delimiter=',', skip_header=2, names=legend, dtype=None)

    i = 0
    plt.suptitle('Buffer size = ' + sizeof_fmt(buffersize), fontsize=16)
    for metric in legend:
        if metric == 'latency':
            continue
        plt.subplot(2, 2, i)
        for trace in traces:
            plt.scatter(values[trace][metric], values[trace]['latency'], color=colors[trace],
                        alpha=0.1, label=names[trace])
        plt.title('Latency according to ' + metric)
        plt.xlabel(metric)
        plt.ylabel('Latency in ns')
        plt.ylim(ymin=750, ymax=3500)
        if metric in x_min and metric in x_max:
            plt.xlim(xmin=x_min[metric], xmax=x_max[metric])
        # plt.legend(prop=fontP)
        i += 1
        plt.subplots_adjust(left=0.06, right=0.94, bottom=0.06)
    # plt.legend(bbox_to_anchor=(1, 0), loc=1, borderaxespad=0.)
    plt.legend(loc=4, borderaxespad=0., fontsize='small')
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(18.5, 10.5, forward=True)
    fig.savefig(str(buffersize) + '.png')
    # plt.show()


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
        #     continue
        if i >= 20500:
            break
        cpu = event['cpu_id']

        if event.name == 'analyze:bufferlist_push_back_begin':
        # if event.name == 'analyze:bufferlist_push_front_begin':
        # if event.name == 'analyze:to_str_begin':
            while cpu >= len(per_cpu_holder):
                per_cpu_holder.append({})

            for metric in metrics:
                if metric not in per_cpu_holder[cpu]:
                    per_cpu_holder[cpu][metric] = -1

                per_cpu_holder[cpu][metric] = event[metric]

            per_cpu_holder[cpu]['time'] = event.timestamp

        if event.name == 'analyze:bufferlist_push_back_end':
        # if event.name == 'analyze:bufferlist_push_front_end':
        # if event.name == 'analyze:to_str_end':
            if 'time' not in results:
                results['time'] = 0
            if cpu >= len(per_cpu_holder):
                continue
            if 'time' not in per_cpu_holder[cpu]:
                continue

            duration = event.timestamp - per_cpu_holder[cpu]['time']
            if duration > 50000:
                continue

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
    print(names[trace])
    print(buffersize)
    pprint(results)
    print('\ntime = ', end='')
    print(results['time'] / total_events)
    for metric in metrics:
        print(metric + ": ", end='')
        print(results[metric] / total_events)

    f.close()


if __name__ == '__main__':
    print('\n\n\n\n\n\n\n\n\n\n\n')
    parser = argparse.ArgumentParser(description='Process traces')
    parser.add_argument('--vector', '-v', type=str, required=True)
    parser.add_argument('--list', '-l', type=str, required=True)
    parser.add_argument('--dequeue', '-d', type=str, required=True)
    parser.add_argument('--buffersize', '-s', type=str, required=True)

    parsed_args = parser.parse_args()

    traces = [parsed_args.vector, parsed_args.list, parsed_args.dequeue]
    colors[parsed_args.vector] = 'red'
    colors[parsed_args.list] = 'green'
    colors[parsed_args.dequeue] = 'purple'
    names[parsed_args.vector] = 'vector'
    names[parsed_args.list] = 'list'
    names[parsed_args.dequeue] = 'dequeue'
    buffersize = parsed_args.buffersize

    for trace in traces:
        count_pmu(trace)
    compile_scatter_plot(final_results)
