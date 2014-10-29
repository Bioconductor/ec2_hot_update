import multiprocessing
import os
import argparse
import sys
import os.path
import subprocess
import signal

num_cores = multiprocessing.cpu_count()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=\
        'Run a command on some instances')
    parser.add_argument('file', 
        help='file listing instance hostnames')
    parser.add_argument('command', 
        help="quoted command to run on each instance")
    parser.add_argument('-k', '--key', dest='key',
        default="~/.ec2/bioc-default.pem",
        help='full path to private key [default ~/.ec2/bioc-default.pem]')
    parser.add_argument("-i") # for ipython hack
    parser.add_argument('-u', '--username', 
        default='ubuntu', help='username to log in as [default ubuntu]')

    args = parser.parse_args()
    if not os.path.isfile(args.file):
        print("No such file: %s" % args.file)
        sys.exit(1)
    with open(args.file) as f:
        instances = [x.strip('\n') for x in f.readlines()]

    def init_worker():
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def runcmd(instance, i):
        cmdargs = ["ssh", "-i", os.path.expanduser(args.key), "-o",
            "StrictHostKeyChecking=no", "%s@%s" % (args.username, instance),
            args.command]
        p = subprocess.Popen(cmdargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate()
        result = p.returncode
        res = """begin output from %s
-----------------
result code: %s
stderr/stdout:
%s
""" % (instance, result, output)
        return(res)

    pool = multiprocessing.Pool(num_cores, init_worker)

    count = 0
    try:
        results = [pool.apply_async(runcmd, (i, 1)) for i in instances]
    except KeyboardInterrupt:
        print("got ^C, exiting")
        pool.terminate()
        sys.exit(1)

    print "\n\n-------Done sending jobs to pool--------------\n\n"
    for r in results:
        count = count + 1
        print '\t', r.get()
    print

    print("got %s results" % count)