__author__ = 'yijunzhu'

import os, sys
import time, datetime, re
import subprocess,optparse
import pexpect

########SSH logon stuff############
default_passwd = "rootroot"
prompt_firstlogin = "Are you sure you want to continue connecting \(yes/no\)\?"
prompt_passwd = "root@.*'s password:"
prompt_logined = "\[root@.*\]#"
prompt_percentage = ".*100%.*"



def SSHClient(IP,prompt=prompt_logined):
    try:
        result = ""
        ssh = pexpect.spawn('ssh root@%s' % IP)
        result = ssh.expect([prompt_firstlogin, prompt_passwd, prompt, pexpect.TIMEOUT],timeout=2000)

        ssh.logfile = None
        if result == 0:
            ssh.sendline('yes')
            ssh.expect(prompt_passwd)
            ssh.sendline(default_passwd)
            ssh.expect(prompt)

        elif result == 1:
            ssh.sendline(default_passwd)
            ssh.expect(prompt)


        elif result == 2:
            pass
        elif result == 3:
            print "Connection::"+"ssh to %s timeout" %IP
            return result
        return ssh
    except:
        print "result is ",result
        print 'Mismatch BTW default expect or unexpected things happen!'
        debug = "Connection::"+ssh.before[:-1]
        print debug
        return debug
        #sys.exit(0)



def timeout_command(command, timeout):
    """call shell-command and either return its output or kill it
    if it doesn't normally exit within timeout seconds and return None"""
    import signal

    if "ping" in command:
        IP = command.split()[-1]
        cmd = "Ping"
    elif "curl" in command:
        IP = re.compile(r'(?<=http:\/\/).*?(?=\/)').findall(command)[0]
        cmd = "Curl"

    else:
        print "error happen"
        sys.exit(0)

    start = datetime.datetime.now()
    # print "start subprocess"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while process.poll() is None:
        now = datetime.datetime.now()
        j = (now - start).seconds
        if (now - start).seconds > timeout:
            os.kill(process.pid, signal.SIGKILL)
            os.waitpid(-1, os.WNOHANG)

            print "cz::debug::%s timeout!!!!!" % (command)
            return "Failed::" + cmd + "::" + IP

    resp = process.stdout.read()
    print resp
    if 'curl' in command:
        if 'HTTP/1.1' not in resp:
            return "Failed::" + cmd + "::" + IP


    return "Passed::" + cmd + "::" + IP


def execute(sip,eip):
    ip_start = sip.split('.')[-1]
    ip_end = eip.split('.')[-1]
    ip_net = '.'.join(sip.split('.')[:-1])

    list = []
    for i in range(int(ip_start),int(ip_end)+1):

        cmd1 = "ping -c 3 -i 1 %s.%d" % (ip_net,i)
        cmd2 = 'curl -i -X PUT -H "X-Auth-Admin-User: .super_admin" -H "X-Auth-Admin-' \
           'Key: rootroot" -H "X-Account-Suffix: zhu-yi-jun" http://%s.%d/auth/v2/zy' \
           'j_acount1' % (ip_net,i)

        print "~~~~~~~~~~~~~~~~~~~~~~~%s~~~~~~~~~~~~~~~~~~~~" % (cmd1)
        cnt1 = timeout_command(cmd1,5)
        list.append(cnt1)
        print "~~~~~~~~~~~~~~~~~~~~~~~%s~~~~~~~~~~~~~~~~~~~~" % (cmd2)
        cnt2 = timeout_command(cmd2,5)
        list.append(cnt2)

        if "Failed" not in cnt1:
            print "~~~~~~~~~~~~~~~~~~~~~~~NTP setting~~~~~~~~~~~~~~~~~~~~"
            ssh = SSHClient('%s.%d' % (ip_net,i))
            if type(ssh) == str:
                ssh.sendline("ntpstat")
                ssh.expect(prompt_logined)
                content = ssh.before[:-1]
                print content

                ssh.sendline("hostname")
                ssh.expect(prompt_logined)
                name = ssh.before[:-1]

                ID = name.split()[-1]
                if 'unsynchronised' in content:
                    list.append('%s is NOT Sync with NTP server' % ID)
                elif "synchronised to NTP server" in content:
                    list.append('%s is Sync' % ID)
                ssh.close()
            else:
                list.append('Unknown ID... ')

        else:
            list.append('Unknown ID... ')


    return list




if __name__ == '__main__':
    usage ="""
example: %prog -s "192.169.220.2" -e "192.169.220.30"
"""
    parser = optparse.OptionParser(usage)

    parser.add_option("-s", "--StartIP", dest="SiP",
                      default='Null',action="store",
                      help="the Input Start IP address specified by user")
    parser.add_option("-e", "--EndIP", dest="EiP",
                      default='Null',action="store",
                      help="the Input End IP address specified by user")



    (options, args) = parser.parse_args()

    argc = len(args)
    if argc != 0:
        parser.error("incorrect number of arguments")
        print usage
    else:
        if options.SiP != "Null" and options.EiP != "Null":
            result = execute(options.SiP, options.EiP)

            for i in result:
                print i
        else:
            print usage

