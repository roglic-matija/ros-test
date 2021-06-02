#!/usr/bin/env python3
# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

## ROS message source code generation for C++
## 
## Converts ROS .msg files in a package into C++ source code implementations.

import msg_gen as genmsg_cpp
 
import sys
import os
import traceback

# roslib.msgs contains the utilities for parsing .msg specifications. It is meant to have no rospy-specific knowledge
import roslib.srvs
import roslib.packages
import roslib.gentools
from rospkg import RosPack

try:
    from cStringIO import StringIO #Python 2.x
except ImportError:
    from io import StringIO #Python 3.x

def write_begin(s, spec, file):
    """
    Writes the beginning of the header file: a comment saying it's auto-generated and the include guards
    
    @param s: The stream to write to
    @type s: stream
    @param spec: The spec
    @type spec: roslib.srvs.SrvSpec
    @param file: The file this service is being generated for
    @type file: str 
    """
    s.write("/* Auto-generated by genmsg_cpp for file %s */\n"%(file))
    s.write('#ifndef %s_SERVICE_%s_H\n'%(spec.package.upper(), spec.short_name.upper()))
    s.write('#define %s_SERVICE_%s_H\n'%(spec.package.upper(), spec.short_name.upper()))

def write_end(s, spec):
    """
    Writes the end of the header file: the ending of the include guards
    
    @param s: The stream to write to
    @type s: stream
    @param spec: The spec
    @type spec: roslib.srvs.SrvSpec
    """
    s.write('#endif // %s_SERVICE_%s_H\n'%(spec.package.upper(), spec.short_name.upper()))
    
def write_generic_includes(s):
    """
    Writes the includes that all service need
    
    @param s: The stream to write to
    @type s: stream
    """
    s.write('#include "ros/service_traits.h"\n\n')
    
def write_trait_char_class(s, class_name, cpp_msg, value):
    """
    Writes a class trait for traits which have static value() members that return const char*
    
    e.g. write_trait_char_class(s, "MD5Sum", "std_srvs::Empty", "hello") yields:
    template<>
    struct MD5Sum<std_srvs::Empty> 
    {
        static const char* value() { return "hello"; }
        static const char* value(const std_srvs::Empty&) { return value(); }
    };
    
    @param s: The stream to write to
    @type s: stream
    @param class_name: The name of the trait class
    @type class_name: str
    @param cpp_msg: The C++ message declaration, e.g. "std_srvs::Empty"
    @type cpp_msg: str
    @param value: The string value to return from the value() function
    @type value: str
    """
    s.write('template<>\nstruct %s<%s> {\n'%(class_name, cpp_msg))
    s.write('  static const char* value() \n  {\n    return "%s";\n  }\n\n'%(value))
    s.write('  static const char* value(const %s&) { return value(); } \n'%(cpp_msg))
    s.write('};\n\n')
    
def write_traits(s, spec, cpp_name_prefix, rospack=None):
    """
    Write all the service traits for a message
    
    @param s: The stream to write to
    @type s: stream
    @param spec: The service spec
    @type spec: roslib.srvs.SrvSpec
    @param cpp_name_prefix: The C++ prefix to prepend when referencing the service, e.g. "std_srvs::"
    @type cpp_name_prefix: str
    """
    gendeps_dict = roslib.gentools.get_dependencies(spec, spec.package, rospack=rospack)
    md5sum = roslib.gentools.compute_md5(gendeps_dict, rospack=rospack)
    
    s.write('namespace ros\n{\n')
    s.write('namespace service_traits\n{\n')
    
    request_with_allocator = '%s%s_<ContainerAllocator> '%(cpp_name_prefix, spec.request.short_name)
    response_with_allocator = '%s%s_<ContainerAllocator> '%(cpp_name_prefix, spec.response.short_name)
    
    write_trait_char_class(s, 'MD5Sum', '%s%s'%(cpp_name_prefix, spec.short_name), md5sum);
    write_trait_char_class(s, 'DataType', '%s%s'%(cpp_name_prefix, spec.short_name), spec.full_name);
    genmsg_cpp.write_trait_char_class(s, 'MD5Sum', request_with_allocator, md5sum)
    genmsg_cpp.write_trait_char_class(s, 'DataType', request_with_allocator, spec.full_name)
    genmsg_cpp.write_trait_char_class(s, 'MD5Sum', response_with_allocator, md5sum)
    genmsg_cpp.write_trait_char_class(s, 'DataType', response_with_allocator, spec.full_name)
    s.write('} // namespace service_traits\n')
    s.write('} // namespace ros\n\n')

def generate(srv_path):
    """
    Generate a service
    
    @param srv_path: the path to the .srv file
    @type srv_path: str
    """
    (package_dir, package) = roslib.packages.get_dir_pkg(srv_path)
    (_, spec) = roslib.srvs.load_from_file(srv_path, package)
    
    s = StringIO()  
    cpp_prefix = '%s::'%(package)
    write_begin(s, spec, srv_path)
    genmsg_cpp.write_generic_includes(s)
    write_generic_includes(s)
    genmsg_cpp.write_includes(s, spec.request)
    s.write('\n')
    genmsg_cpp.write_includes(s, spec.response)
    
    rospack = RosPack()
    gendeps_dict = roslib.gentools.get_dependencies(spec, spec.package, rospack=rospack)
    md5sum = roslib.gentools.compute_md5(gendeps_dict, rospack=rospack)
    
    s.write('namespace %s\n{\n'%(package))
    genmsg_cpp.write_struct(s, spec.request, cpp_prefix, {'ServerMD5Sum': md5sum})
    genmsg_cpp.write_constant_definitions(s, spec.request)
    s.write('\n')
    genmsg_cpp.write_struct(s, spec.response, cpp_prefix, {'ServerMD5Sum': md5sum})
    genmsg_cpp.write_constant_definitions(s, spec.response)
    s.write('struct %s\n{\n'%(spec.short_name))
    s.write('\n')
    s.write('typedef %s Request;\n'%(spec.request.short_name))
    s.write('typedef %s Response;\n'%(spec.response.short_name))
    s.write('Request request;\n')
    s.write('Response response;\n\n')
    s.write('typedef Request RequestType;\n')
    s.write('typedef Response ResponseType;\n')
    s.write('}; // struct %s\n'%(spec.short_name))
    s.write('} // namespace %s\n\n'%(package))
    
    request_cpp_name = "Request"
    response_cpp_name = "Response"
    genmsg_cpp.write_traits(s, spec.request, cpp_prefix, rospack=rospack)
    s.write('\n')
    genmsg_cpp.write_traits(s, spec.response, cpp_prefix, rospack=rospack)
    genmsg_cpp.write_serialization(s, spec.request, cpp_prefix)
    s.write('\n')
    genmsg_cpp.write_serialization(s, spec.response, cpp_prefix)
    
    write_traits(s, spec, cpp_prefix, rospack=rospack)
    
    write_end(s, spec)
    
    output_dir = '%s/srv_gen/cpp/include/%s'%(package_dir, package)
    if (not os.path.exists(output_dir)):
        # if we're being run concurrently, the above test can report false but os.makedirs can still fail if
        # another copy just created the directory
        try:
            os.makedirs(output_dir)
        except OSError as e:
            pass
        
    f = open('%s/%s.h'%(output_dir, spec.short_name), 'w')
    f.write(s.getvalue() + "\n")
    
    s.close()

def generate_services(argv):
    for arg in argv[1:]:
        generate(arg)

if __name__ == "__main__":
    roslib.msgs.set_verbose(False)
    generate_services(sys.argv)
    
    
