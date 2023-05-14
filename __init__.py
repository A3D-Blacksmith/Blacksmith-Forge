'''
Copyright (c) 2018-2023 Naxela

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.
'''

bl_info = {
    'name': 'BMForge',
    'description': 'BMForge.',
    'author': 'Alexander Kleemann @ Naxela',
    'version': (0, 0, 2),
    'blender': (3, 30, 0),
    'location': 'View3D',
    'category': '3D View'
}

import os, sys, bpy, time, threading, socket, json, multiprocessing, subprocess, threading
from typing import Callable

from bpy.utils import ( register_class, unregister_class )
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    EnumProperty,
    PointerProperty,
)
from bpy.types import (
    Panel,
    AddonPreferences,
    Operator,
    PropertyGroup,
)


BM_STATUS = {
    "active" : False,
    "thread" : None,
    "socket" : None
}


class BM_Properties (PropertyGroup):

    Server_Running : BoolProperty(
        name="Server running",
        description="Prop.",
        default = False
    )

def broadcast(connection, msg, prefix=""):  # prefix is for name identification.

    connection.send(bytes(prefix, "utf8") + msg)

def evaluateCommand(input, header):
    if input == 0: #Shutdown

        print("Shutting down")

        try:
            BM_STATUS["socket"].close()
        except:
            pass
        BM_STATUS["active"] = False
        BM_STATUS["thread"].join()

    elif input == 1: #Append file

        print("Appending scene")

        filepath = header

        with bpy.data.libraries.load(filepath) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects]

        # link them to scene
        scene = bpy.context.scene
        for obj in data_to.objects:
            if obj is not None:
                bpy.context.collection.objects.link(obj)

    #TODO - CHECK MENU LIST IN BM Client

    if input == 2: #Append object

        print("Added object")

    if input == 3: #Add Environment

        print("Added environment")

    if input == 4: #Add Textures

        print("Added environment")

    if input == 5: #Add nodegroup

        print("Added nodegroup")

def run_proc(cmd) -> subprocess.Popen:
    """Creates a subprocess with the given command and returns it.
    If Blender is not running in background mode, a thread is spawned
    that waits until the subprocess has finished executing to not freeze
    the UI, otherwise (in background mode) execution is blocked until
    the subprocess has finished.
    If `done` is not `None`, it is called afterwards in the main thread.
    """

    p = subprocess.Popen(cmd)

    #use_thread = not bpy.app.background
    # use_thread = True

    # def wait_for_proc(proc: subprocess.Popen):
    #     proc.wait()

    #     if use_thread:
    #         # Put the done callback into the callback queue so that it
    #         # can be received by a polling function in the main thread
    #         thread_callback_queue.put([threading.current_thread(), done], block=True)
    #     else:
    #         done()

    # print(*cmd)
    # p = subprocess.Popen(cmd)

    # if use_thread:
    #     threading.Thread(target=wait_for_proc, args=(p,)).start()
    # else:
    #     wait_for_proc(p)

    return p

def startServer():

    BM_STATUS["socket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  

    BM_STATUS["socket"].bind(('127.0.0.1', 12345))  
    BM_STATUS["socket"].listen(1)
    print("Starting server")

    BM_STATUS["active"] = True

    while BM_STATUS["active"]:

        connection, address = BM_STATUS["socket"].accept()  

        print("Connection from: %s:%s" % address)

        while BM_STATUS["active"]:

            print("Listening")
            try:
                data = connection.recv(1024)
            except:
                print("Bad error occurred A")

            if data != bytes("#quit", "utf8"):

                try:
                    parsed_data = json.loads(data.decode())
                except:
                    print("Bad error occurred B")

                print(parsed_data)

                if parsed_data['action'] == 0: #Ping

                    #print("BMForge: Ping")
                    print("Ping header: " + parsed_data['header'])

                elif parsed_data['action'] == 1: #Query

                    #print("BMForge: Query")
                    print("Query header: " + parsed_data['header'])

                elif parsed_data['action'] == 2: #Command

                    #print("BMForge: Command")
                    print("Command header: " + parsed_data['header'])
                    evaluateCommand(parsed_data['command'], parsed_data['header'])

                else:

                    print("BMForge: Unknown call")
                    BM_STATUS["active"] = False
                    connection.close()

                #broadcast(connection, data, name + ": ")

            else:

                print("Quitting")
                connection.send(bytes("#quit", "utf8"))
                connection.close()
                broadcast(connection, bytes("%s has left the chat." % name, "utf8"))

                break

    BM_STATUS["socket"].close()

    print("Socket closed")

class BM_Connect(bpy.types.Operator):
    bl_idname = "bm.connect"
    bl_label = "Connect to Blacksmith"
    bl_description = "Connect to Blacksmith"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        #file_dir = os.path.dirname(os.path.realpath(__file__))
        #run_proc(os.path.join(file_dir, "runtime/nw.exe"))

        BM_STATUS["thread"] = threading.Thread(target=startServer)
        BM_STATUS["thread"].daemon = True
        BM_STATUS["thread"].start()

        return {'FINISHED'}

class BM_Close(bpy.types.Operator):
    bl_idname = "bm.close"
    bl_label = "Close connection"
    bl_description = "Close connection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        try:
            BM_STATUS["socket"].close()
        except:
            pass
        BM_STATUS["active"] = False
        BM_STATUS["thread"].join()

        return {'FINISHED'}

class SCENE_PT_BM_panel (Panel):
    bl_idname = "SCENE_PT_BM_panel"
    bl_label = "BMForge"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BMForge"

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row(align=True)
        if BM_STATUS["active"] == False:
            row.operator("bm.connect")
        else:
            row.operator("bm.close")

classes = [BM_Connect, BM_Close, SCENE_PT_BM_panel]

def register():
    for cls in classes:
        register_class(cls)

def unregister():
    for cls in reversed(classes):
        unregister_class(cls)