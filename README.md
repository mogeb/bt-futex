# bt-futex
Account time spent in `sys_futex` using Babeltrace

You need to have LTTng installed, and Babeltrace installed with Python bindings.

#### Trace futex calls
```
lttng create -o .
lttng enable-channel --num-subbuf 16 --subbuf-size 2M -k c0
lttng enable-event sched_switch -k -c c0
lttng enable-event --syscall futex -k -c c0
lttng start
# do stuff..
lttng stop
lttng destroy
```


#### View futex calls
```
$> python3 count_futex.py kernel/
PROCESS_NAME (TID): LOCK_TIME ns
git (17550):  2,122
git (17551):  8,124
example (17554):  80,690,708
example (17555):  80,020,536
example (17556):  367,010,253
example (17557):  459,009,153
example (17558):  199,676,209
example (17559):  108,401
example (17560):  475,562,084
example (17561):  80,549,102
example (17562):  468,002,252
example (17564):  92,108,616
example (17566):  450,655,745
example (17567):  49,904,388
libvirtd (3772):  2,389
libvirtd (3773):  2,839
libvirtd (3775):  2,417
libvirtd (3776):  3,577
libvirtd (3777):  2,492
```
