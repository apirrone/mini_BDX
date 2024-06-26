import os
import time
from queue import Queue
from threading import Thread

import mujoco
import mujoco.viewer
import numpy as np
from scipy.spatial.transform import Rotation as R


class BDXMujocoServer:
    def __init__(self, model_path="../../mini_bdx/robots/bdx/", gravity_on=True):
        self.model = mujoco.MjModel.from_xml_path(os.path.join(model_path, "scene.xml"))
        self.data = mujoco.MjData(self.model)
        self.actions_queue = Queue()

        self.gravity_on = gravity_on

        self.viewer = mujoco.viewer.launch_passive(
            self.model, self.data, key_callback=self.key_callback
        )
        self.sim_speed = 1
        self.dt = 0
        if not self.gravity_on:
            self.model.opt.gravity[:] = [0, 0, 0]
        self.key_pressed = None
        self.key_pressed_timeout = 0

    def key_callback(self, keycode):
        self.key_pressed = keycode
        self.key_pressed_timeout = 0.1
        if keycode == 80:  # p
            self.sim_speed += 0.1
            print("sim speed : ", self.sim_speed)
        if keycode == 79:  # o
            self.sim_speed = max(0.005, self.sim_speed - 0.1)
            print("sim speed : ", self.sim_speed)
        if keycode == 71:  # g
            self.gravity_on = not self.gravity_on
            if self.gravity_on:
                self.model.opt.gravity[:] = [0, 0, -9.81]
            else:
                self.model.opt.gravity[:] = [0, 0, 0]

    def start(self):
        Thread(target=self.run, daemon=True).start()

    def run(self):
        prev = self.data.time
        while True:
            self.dt = self.data.time - prev
            self.key_pressed_timeout -= self.dt
            if self.key_pressed_timeout < 0:
                self.key_pressed = None
            try:
                actions = self.actions_queue.get(block=False)
                self.data.ctrl[:] = actions
            except Exception:
                pass

            prev = self.data.time
            mujoco.mj_step(self.model, self.data, 4)
            self.viewer.sync()
            # time.sleep(0.0001 * (1 / self.sim_speed))

    def send_action(self, action):
        self.actions_queue.put(action)

    def get_state(self):
        return self.data.qpos.flat.copy(), self.data.qvel.flat.copy()

    def get_imu(self):

        rot_mat = np.array(self.data.body("base").xmat).reshape(3, 3)
        gyro = R.from_matrix(rot_mat).as_euler("xyz")

        accelerometer = np.array(self.data.body("base").cvel)[3:]

        return gyro, accelerometer

    def get_feet_contact(self):
        right_contact = self.check_contact("foot_module", "floor")
        left_contact = self.check_contact("foot_module_2", "floor")
        return right_contact, left_contact

    def check_contact(self, body1_name, body2_name):
        body1_id = self.data.body(body1_name).id
        body2_id = self.data.body(body2_name).id
        for i in range(self.data.ncon):
            try:
                contact = self.data.contact[i]
            except Exception as e:
                return False

            if (
                self.model.geom_bodyid[contact.geom1] == body1_id
                and self.model.geom_bodyid[contact.geom2] == body2_id
            ) or (
                self.model.geom_bodyid[contact.geom1] == body2_id
                and self.model.geom_bodyid[contact.geom2] == body1_id
            ):
                return True

        return False


if __name__ == "__main__":
    server = BDXMujocoServer()
    while True:
        server.send_action([0.5] * 13)
        time.sleep(0.1)
