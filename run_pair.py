import logging
from argparse import ArgumentParser
import sys,os
from pcaspy import SimpleServer
from pcaspy.tools import ServerThread
import ioc_merge
from cueye import ueyeCam 
#from daemon import Daemon


parser = ArgumentParser()

parser.add_argument("--ioc_prefix", type=str, help="Prefix of the IOC.")
parser.add_argument("--ioc_prefix1", type=str, help="Prefix for camera 1.")
parser.add_argument("--ioc_prefix2", type=str, help="Prefix for camera 2.")
parser.add_argument("--boardnr1", type=str, help="board number of camera 1")
parser.add_argument("--boardnr2", type=str, help="board number of camera 2")
parser.add_argument("--log_level", default="WARNING", choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], help="Log level to use.")
arguments = parser.parse_args()

logging.basicConfig(stream=sys.stdout, level=arguments.log_level)
_logger = logging.getLogger(arguments.ioc_prefix)
_logger.info("Starting ioc with prefix %s", arguments.ioc_prefix)


#Loading both cameras
_logger.info("Loading camera %s with subprefix: %s"%(arguments.boardnr1, arguments.ioc_prefix1))
cam1=ueyeCam(arguments.boardnr1)
if cam1.status:
	_logger.error("Error on 1st ccd")
	sys.exit()

_logger.info("Loading camera %s with subprefix: %s"%(arguments.boardnr2, arguments.ioc_prefix2))
cam2=ueyeCam(arguments.boardnr2)
print(cam2.status)
if cam2.status:
	_logger.error("Error on 2nd ccd")
	sys.exit()

pvs=ioc_merge.make_pvs(arguments.ioc_prefix1)
pvs.update(ioc_merge.make_pvs(arguments.ioc_prefix2))

server = SimpleServer()
server.createPV(prefix=arguments.ioc_prefix, pvdb=pvs)

driver = ioc_merge.iocMerge([[cam1, arguments.ioc_prefix1], [cam2, arguments.ioc_prefix2]] )
server_thread = ServerThread(server)
server_thread.start()

	


if __name__ == "__main__":
	while not(raw_input("Press 'q' to quit: ")=='q'):
		pass

	_logger.info("User requested ioc termination. Exiting.")
	server_thread.stop()
	cam1.stopAcq()
	cam2.stopAcq()
	sys.exit()
	

	
	
