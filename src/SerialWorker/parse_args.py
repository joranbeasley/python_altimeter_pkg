import argparse
import sys
flags={}
p = argparse.ArgumentParser()
def validate_namespace(inst,ns):
    if ns.BW is not None and ns.Ns is not None:
        maxDist = 75.0*ns.Ns/ns.BW
        if not flags.get('maxDist'):
            flags['maxDist'] = maxDist
            print("# Estimated Theoretical max dist = %s"%maxDist)
        if ns.Rmax is not None:
            if maxDist < ns.Rmax:
                ns0 = int(ns.Rmax*ns.BW/75.0)+1
                bw0 = int(75.0*ns.Ns/ns.Rmax)
                raise argparse.ArgumentError(inst,("INVALID Rmax for given BW and f0\n"
                                                  "Theoretical MaxDist: %s = 75.0 * {Ns}/{BW} = 75.0 * %s/%s\n"
                                                  "To have a max dist of %s you need {NS >= %s;BW=%s} or {BW < %s;BW=%s}\n"
                                                   )%(maxDist,ns.Ns,ns.BW,ns.Rmax,ns0,ns.BW,bw0,ns.Ns)
                                             )
    if ns.BW is not None and ns.f0 is not None:
        maxBW = 245-ns.f0
        if maxBW < ns.BW:
            raise argparse.ArgumentError(inst,"INVALID BW for f0\nmaxBW= 245 - {f0} = %s\nBW=%s;f0=%s"%(maxBW,ns.BW,ns.f0))

class URADAction(argparse.Action):
     def __init__(self, option_strings, dest=None, nargs=None,minimum=None,maximum=None, **kwargs):
         if nargs is not None:
             raise ValueError("nargs not allowed")
         # print(option_strings, dest, kwargs)
         self.range=[minimum or float("-inf"),maximum or float("inf")]
         #kwargs.pop('prog')
         super(URADAction, self).__init__(option_strings, dest, **kwargs)
     def __call__(self, parser, namespace, values, option_string=None):
         try:
             if not self.range[0] <= values <= self.range[1]:
                raise argparse.ArgumentError(self,"Argument %s = %r not in range [%s .. %s] "%(option_string,values,self.range[0],self.range[1]))
         except TypeError:
             # print(namespace,values,option_string)
             raise argparse.ArgumentError(self, "Argument %s Exception : %s between %r"%(option_string,values,self.range))
         setattr(namespace, self.dest, values)
         validate_namespace(self,namespace)
         # if self.dest == 'f0':
         #     if namespace.BW is not None:
         #         maxBW = 245-values
         #         if namespace.BW > maxBW:
         #             raise argparse.ArgumentError(self,"f0 of %d incompatible with BW > %d, but BW is set to %s"%(values,maxBW,namespace.BW))
         #     # print("CHECK:",namespace)
         #     if namespace.mode is not None:
         #         if namespace.mode != 1 and values > 195:
         #             raise argparse.ArgumentError(self,
         #                 "the max f0 value of all modes other than 1 is 195 you have supplied f0=%r, mode=%r" % (
         #                     values,namespace.mode))
         # elif self.dest == "BW":
         #     if namespace.f0 is not None:
         #         maxBW = 245 - namespace.f0
         #         if values > maxBW:
         #             raise argparse.ArgumentError(self,
         #                 "f0 of %d incompatible with BW > %d, but BW is set to %s" % ( namespace.f0, maxBW, values))
         #     if namespace.Ns is not None:
         #         print "# Estimated max theoretical distance=75*Ns/BW=%s"%(int(float(75)*values/namespace.BW))
         # elif self.dest == "mode":
         #     if namespace.Rmax is not None:
         #         if namespace.Rmax > 75 and values == 1:
         #             raise argparse.ArgumentError("max Rmax when using mode=1 is 75, but you sent Rmax=%s"%(namespace.Rmax,))
         #     if namespace.f0 is not None:
         #         if values != 1 and namespace.f0 > 195:
         #            raise argparse.ArgumentError(self,"the max f0 value of all modes other than 1 is 195 you have supplied f0=%r, mode=%r"%(namespace.f0,values))
         # if self.dest == "Ns":
         #     if namespace.BW is not None:
         #         print "# Estimated max theoretical distance=75*Ns/BW=%s"%(int(75*values/namespace.BW))
         # if self.dest == "Rmax":
         #     if namespace.mode is not None:
         #         if values > 75 and namespace.mode == 1:
         #             raise argparse.ArgumentError(self,"max Rmax when using mode=1 is 75, but you sent Rmax=%s"%(values,))
         #     if namespace.BW is not None and namespace.Ns is not None:
         #         maxDist= 75*float(namespace.Ns)/namespace.BW




         # print '%r %r %r %r' % (namespace, values, option_string, self.dest)
def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
def setup_arguments():
    g0 = p.add_subparsers(help='command',dest='subparser_cmd')
    group_run = g0.add_parser("run",help="run the program")
    group_run.add_argument("-s","--smartmicro",help="smartmicro altimeter port", metavar="COM5", required=False,type=str,default="/dev/altimeter",action="store")
    group_run.add_argument("-u","--urad",help="urad altimeter port", metavar="/dev/urad",required=False,type=str,default="/dev/urad",action="store")
    group_run.add_argument("-b","--bu",help="BU-353S4 gps port",metavar="COM4",default="/dev/gps",required=False,type=str,action="store")
    #
    g1 = g0.add_parser('update', help="update the redis-cli and exit")
    # g1 = group_upd.add_mutually_exclusive_group()
    group_upd = g1.add_subparsers(help="what",dest="subparser_what")
    reading_g = group_upd.add_parser("reading", help="update the active reading")
    reading_g.add_argument("-a", "--altitude_ground", type=float, required=False,action="store")
    reading_g.add_argument('-b', "--altitude_sealevel", type=float, required=False,action="store")
    reading_g.add_argument('-g', '--geiod_height', type=float, required=False,action="store")
    reading_g.add_argument('-l', '--latitude', type=float, required=False,action="store")
    reading_g.add_argument('-n', '--longitude', type=float, required=False,action="store")
    reading_g.add_argument('-q', '--num-sat',dest="num_satellites", type=int, required=False,action="store")
    reading_g.add_argument('-s', '--sat-signal', type=int, required=False,action="store")
    #
    devices_g = group_upd.add_parser("connect", help="update connected devices")
    devices_g.add_argument('-a',"--altimeter", required=False,action="store_true")
    devices_g.add_argument('-g',"--gps", required=False,action="store_true")
    devices_g.add_argument('-u','--usb', required=False,action="store_true")
    devices_g = group_upd.add_parser("disconnect", help="update connected devices")
    devices_g.add_argument('-a', "--altimeter", required=False, action="store_true")
    devices_g.add_argument('-g', "--gps", required=False, action="store_true")
    devices_g.add_argument('-u', '--usb', required=False, action="store_true")
    urad_g = group_upd.add_parser("urad", help="update urad configuration")
    urad_g.add_argument('-m', '--mode', choices=[1, 2, 3, 4], metavar="[1-4]",
                        type=int, help="The mode (1-4)", action=URADAction)
    urad_g.add_argument('-f', '--f0',  type=int,metavar="[5-245]",
                        help="f0 if mode=1 max is 245, for all other modes max is 195",
                        action=URADAction
                        )
    urad_g.add_argument('-B', '--BW', type=int, minimum=50, maximum=240,
                        metavar="[50-240]",
                        help="The BW (50-240) maxBW is 245-f0", action=URADAction)
    urad_g.add_argument("-N",'--Ns', type=int, minimum=50, maximum=200, action=URADAction, metavar="[50-200]", help="Num samples")
    urad_g.add_argument("-n",'--ntar',dest="Ntar", type=int, choices=[1,2,3,4,5],metavar="[1-5]")
    urad_g.add_argument("-R",'--Rmax', type=int, minimum=0, maximum=100, help="DISTANCE to detect (in mode=1 max is 75)", action=URADAction)
    urad_g.add_argument("-t",'--MTI', type=str2bool,help="Enable Moving Target Tracking")
    urad_g.add_argument("-M",'--Mth', type=int,choices=range(1,5),help="Moving Target Tracking Sensitivity",metavar="[1-5]")
    urad_g.add_argument("-A",'--Alpha', type=int, minimum=3, maximum=25, action=URADAction, help="restrictiveness of peak detection senitivity", metavar="[3-25]")
    urad_g.add_argument("-o",'--output', type=str, help="update or create urad_config.txt file", metavar="/boot/urad_config.txt")
    urad_g.add_argument('--redis', help="send redis event for SerialWorker/main",action="store_true")

    #reading_g.add_argument('-g', 'geiod_height', type=float, required=False)
def parse_args():
    args = list(sys.argv)
    if len(args) < 2:
        args.append("run",)
    elif args[1].startswith("-"):
        args.insert(1,"run")
    setup_arguments()
    return p.parse_args(args[1:])

def handle_args(args):
    if args.subparser_cmd == "run":
        print ("RUN APPLICATION",args)
    if args.subparser_cmd == "update":
        if args.subparser_what == "reading":
            print("UPDATE READING:",args)
            import pdb;pdb.set_trace()
        elif args.subparser_what == "connect":
            print("UPD DEVICES:",args)
    print(args)
if __name__ == "__main__":
    handle_args(parse_args())
