import argparse, yaml, telnetlib, time, threading, sys
from datetime import datetime
from influxdb import InfluxDBClient

with open('PerfAgent.yaml', 'r') as theYaml:
    influxdbConfig = yaml.load(theYaml)

parser = argparse.ArgumentParser()
parser.add_argument('agent_ip')
parser.add_argument('agent_port')
parser.add_argument('duration')
parser.add_argument('interval')
args = parser.parse_args()

endTime = time.time() + int(args.duration)

INFLUXDB_HOST = influxdbConfig['Configs']['influxdb_host']
INFLUXDB_PORT = influxdbConfig['Configs']['influxdb_port']
INFLUXDB_LOGIN = influxdbConfig['Configs']['influxdb_login']
INFLUXDB_PASSWORD = influxdbConfig['Configs']['influxdb_password']
INFLUXDB_DATABASE = influxdbConfig['Configs']['influxdb_database']
TELNET_TIMEOUT = influxdbConfig['Configs']['telnet_timeout']
ENVIRONMENT = influxdbConfig['Configs']['environment']

influxClient = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_LOGIN, INFLUXDB_PASSWORD, INFLUXDB_DATABASE, use_udp=True, udp_port=4444)

tn_cpu_session = telnetlib.Telnet(args.agent_ip, args.agent_port, TELNET_TIMEOUT)
tn_mem_session = telnetlib.Telnet(args.agent_ip, args.agent_port, TELNET_TIMEOUT)
tn_tcp_session = telnetlib.Telnet(args.agent_ip, args.agent_port, TELNET_TIMEOUT)

#tn_cpu_session.write('test'+'\n')
tn_cpu_session.write('interval:' + args.interval + '\n')
tn_mem_session.write('interval:' + args.interval + '\n')
tn_tcp_session.write('interval:' + args.interval + '\n')

def write_to_influxdb():

    if time.time() >= endTime:
        tn_cpu_session.write('exit'+'\n')
        tn_mem_session.write('exit'+'\n')
        tn_tcp_session.write('exit'+'\n')
        sys.exit('goodbye')
    
    tn_cpu_session.write('metrics-single:cpu:combined'+'\n')
    tn_mem_session.write('metrics-single:memory:usedperc'+'\n')
    tn_tcp_session.write('metrics-single:tcp:estab'+'\n')

    tn_cpu_resp = tn_cpu_session.read_until('\n')
    tn_mem_resp = tn_mem_session.read_until('\n')
    tn_tcp_resp = tn_tcp_session.read_until('\n')

    tn_cpu_resp = round(float(tn_cpu_resp.strip()))
    tn_mem_resp = round(float(tn_mem_resp.strip()))
    tn_tcp_resp = round(float(tn_tcp_resp.strip()))

    cpu_json_body = [
        {
            "measurement": "cpu_load",
            "tags": {
                # "environment": influxdbConfig['Configs']['environment'],
                "box": args.agent_ip
            },
            "time": datetime.utcnow(),
            "fields": {
                "value": tn_cpu_resp
            }
        }
    ]

    mem_json_body = [
        {
            "measurement": "memory",
            "tags": {
                # "environment": influxdbConfig['Configs']['environment'],
                "box": args.agent_ip
            },
            "time": datetime.utcnow(),
            "fields": {
                "value": tn_mem_resp
            }
        }
    ]

    tcp_json_body = [
        {
            "measurement": "tcp_connections",
            "tags": {
                # "environment": influxdbConfig['Configs']['environment'],
                "box": args.agent_ip
            },
            "time": datetime.utcnow(),
            "fields": {
                "value": tn_tcp_resp
            }
        }
    ]

    print 'cpu %d' % tn_cpu_resp 
    print 'mem %d' % tn_mem_resp
    print 'tcp %d' % tn_tcp_resp
    print '_' * 20

    tTimer = threading.Timer(float(args.interval), write_to_influxdb).start()

    influxClient.write_points(cpu_json_body, database = INFLUXDB_DATABASE)
    influxClient.write_points(mem_json_body, database = INFLUXDB_DATABASE)
    influxClient.write_points(tcp_json_body, database = INFLUXDB_DATABASE)

write_to_influxdb()
        




