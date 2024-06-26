import argparse
import time

import cv2
import mujoco
import mujoco_viewer
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument(
    "-p-", "--path", type=str, required=True, help="Path to the xml file"
)
args = parser.parse_args()

model = mujoco.MjModel.from_xml_path(args.path)
data = mujoco.MjData(model)


# create the viewer object
viewer = mujoco_viewer.MujocoViewer(
    model, data, mode="window", width=1280, height=800, hide_menus=True
)
dofs = {
    "base_x": 0,
    "base_y": 1,
    "base_z": 2,
    "base_q0": 3,
    "base_q1": 4,
    "base_q2": 5,
    "base_q3": 6,
    "right_hip_yaw": 7,
    "right_hip_roll": 8,
    "right_hip_pitch": 9,
    "right_knee_pitch": 10,
    "right_ankle_pitch": 11,
    "left_hip_yaw": 12,
    "left_hip_roll": 13,
    "left_hip_pitch": 14,
    "left_knee_pitch": 15,
    "left_ankle_pitch": 16,
    "head_pitch1": 17,
    "head_pitch2": 18,
    "head_yaw": 19,
}

init = {
    "right_hip_yaw": 0,
    "right_hip_roll": 0,
    "right_hip_pitch": np.deg2rad(45),
    "right_knee_pitch": np.deg2rad(-90),
    "right_ankle_pitch": np.deg2rad(45),
    "left_hip_yaw": 0,
    "left_hip_roll": 0,
    "left_hip_pitch": np.deg2rad(45),
    "left_knee_pitch": np.deg2rad(-90),
    "left_ankle_pitch": np.deg2rad(45),
    "head_pitch1": np.deg2rad(-45),
    "head_pitch2": np.deg2rad(-45),
    "head_yaw": 0,
}


def goto_init():
    i = 0
    for key, value in init.items():
        data.ctrl[i] = value
        i += 1


def check_contact(body1_name, body2_name):
    body1_id = data.body(body1_name).id
    body2_id = data.body(body2_name).id

    for i in range(data.ncon):
        contact = data.contact[i]

        if (
            model.geom_bodyid[contact.geom1] == body1_id
            and model.geom_bodyid[contact.geom2] == body2_id
        ) or (
            model.geom_bodyid[contact.geom1] == body2_id
            and model.geom_bodyid[contact.geom2] == body1_id
        ):
            return True

    return False


target = [0.5, 0.5, 0.1]
model.opt.gravity[:] = [0, 0, 0]
# data.qpos[6] = np.deg2rad(90)
target = [0, 1, 0.1]
# goto_init()


for i in range(7, len(data.qpos)):
    data.qpos[i] = np.random.uniform(-0.2, 0.2)
    data.ctrl[i - 7] = data.qpos[i]


im = np.zeros((800, 800, 3), dtype=np.uint8)
while True:
    if viewer.is_alive:
        cv2.imshow("image", im)
        key = cv2.waitKey(1)
        if key == 13:
            data.xfrc_applied[data.body("base").id][:3] = [0, 0, 1000]  # absolute
        else:
            data.xfrc_applied[data.body("base").id][:3] = [0, 0, 0]  # absolute

        print(data.qpos)

        # print(check_contact("foot_module", "floor"))

        # print(data.body("base"))

        # goto_init()
        # print(model.nq)
        # data.qpos[1] = 0.22 + 0.2 * np.sin(0.5 * np.pi * time.time())
        # print(np.around(data.body("base").cvel[3:], 2))  # absolute

        # print(np.square(data.body("base").xpos[2] - 0.12) * 100)
        # print(data.qvel[8 : 8 + 10])
        # print(data.body("foot_module"))
        # print(check_contact("base", "floor"))
        # print(data.body("base").cvel[3:])

        # rot = np.array(data.body("base").xmat).reshape(3, 3)
        # Z_vec = rot[:, 2]
        # T = np.eye(4)
        # T[:3, :3] = rot

        # print(len(data.ctrl), data.ctrl)
        # data.ctrl[4] = (np.pi / 4) * (np.sin(2 * np.pi * 1 * data.time) + 1) - np.pi / 4
        # data.ctrl[4] = np.pi / 2

        mujoco.mj_step(model, data)
        viewer.render()
    else:
        break

# close
viewer.close()
