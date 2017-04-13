import babeltrace.reader
import sys
from pprint import pprint

current_thread = {}
tid_wait_time = {}
name_mapping = {}
# while we wait for the exit_futex event
tmp_wait_time = {}
total_time = 0


def usage():
    print('Usage: ' + sys.argv[0] + ' TRACE')


# Stolen from the internet
def intWithCommas(x):
    if type(x) not in [type(0)]:
        raise TypeError("Parameter must be an integer.")
    if x < 0:
        return '-' + intWithCommas(-x)
    result = ''
    while x >= 1000:
        x, r = divmod(x, 1000)
        result = ",%03d%s" % (r, result)
    return "%d%s" % (x, result)


def handle_event(event):
    cpu = event['cpu_id']
    if not cpu in current_thread:
        return

    current_tid = current_thread[cpu]
    if event.name == 'syscall_entry_futex':
        tmp_wait_time[current_tid] = event.timestamp
    if event.name == 'syscall_exit_futex':
        if not current_tid in tmp_wait_time:
            # we missed the futex_entry associated with this futex_exit, ignore
            return
        if not current_tid in tid_wait_time:
            tid_wait_time[current_tid] = 0
        tid_wait_time[current_tid] += event.timestamp - tmp_wait_time[current_tid]


def count_futex(trace):
    trace_collection = babeltrace.reader.TraceCollection()
    trace_collection.add_trace(trace, 'ctf')

    for event in trace_collection.events:
        if event.name == 'sched_switch':
            current_thread[event['cpu_id']] = event['next_tid']
            # build name mapping
            if event['next_tid'] in tid_wait_time:
                name_mapping[event['next_tid']] = event['next_comm']
            if event['prev_tid'] in tid_wait_time:
                name_mapping[event['prev_tid']] = event['prev_comm']
        handle_event(event)

    print('PROCESS_NAME (TID): LOCK_TIME ns')
    # pprint(tid_wait_time, None, 4)
    for k in tid_wait_time:
        print(name_mapping[k] + ' (' + str(k) + '):  ' +
            intWithCommas(tid_wait_time[k]))


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        usage()
        exit()
    count_futex(sys.argv[1])
