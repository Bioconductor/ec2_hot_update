import multiprocessing
import os
import argparse
import sys
import os.path
import subprocess
import StringIO
import signal

num_cores = multiprocessing.cpu_count()

if __name__ == '__main__':
    a = 1


    parser = argparse.ArgumentParser(description='Run a command on some instances')
    parser.add_argument('file', 
                       help='file listing instance hostnames')
    parser.add_argument('command', 
                       help="quoted command to run on each instance")
    parser.add_argument('-k', '--key', dest='key',
                       default="~/.ec2/bioc-default.pem",
                       help='full path to private key [default ~/.ec2/bioc-default.pem')
    parser.add_argument("-i")
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
        # output_fh = StringIO.StringIO()
        res = "instance: %s, cmd: %s" % (instance, args.command)
        cmdargs = ["ssh", "-i", os.path.expanduser(args.key), "-o",
            "StrictHostKeyChecking=no", "%s@%s" % (args.username, instance),
            args.command]
        # try:
        p = subprocess.Popen(cmdargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate()
        result = p.returncode
        # except KeyboardInterrupt:
        #     print("got ^C, exiting")
        #     sys.exit(1)
        res = """begin output from %s
-----------------
result code: %s
stderr/stdout:
%s
""" % (instance, result, output)
        # output_fh.close()
        return(res)

    pool = multiprocessing.Pool(num_cores, init_worker)

    try:
        results = [pool.apply_async(runcmd, (i, 1)) for i in instances]
    except KeyboardInterrupt:
        print("got ^C, exiting")
        pool.terminate()
        sys.exit(1)

    print "\n\n-------Done--------------\n\n"
    for r in results:
        print '\t', r.get()
    print