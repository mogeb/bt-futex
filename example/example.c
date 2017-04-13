#include <stdlib.h>
#include <stdio.h>
#include <pthread.h>
#include <semaphore.h>

sem_t mutex;

void usage(char *arg)
{
    printf("Usage: [%s] num_threads\n", arg);
}

void *do_work(void *arg)
{
    int delay = (int)arg;
    volatile int count;
    printf("%d\n", delay);
    do {
        count =  delay * 100000;
        sem_wait(&mutex);
        while(count--);
        sem_post(&mutex);
    } while (delay--);
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        usage(argv[0]);
        return 1;
    }

    int nthreads, i;
    pthread_t *threads;

    nthreads = atoi(argv[1]);
    threads = malloc(nthreads * sizeof(pthread_t));
    sem_init(&mutex, 0, 1);

    for (i = 0 ; i < nthreads; i++) {
        pthread_create(&threads[i], NULL, do_work, (void*)i);
    }

    for (i = 0; i < nthreads; i++) {
        pthread_join(threads[i], NULL);
    }

    return 0;
}
