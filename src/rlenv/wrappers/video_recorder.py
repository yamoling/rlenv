import os
from datetime import datetime
from typing import Literal
import cv2
from .rlenv_wrapper import RLEnvWrapper, RLEnv


class VideoRecorder(RLEnvWrapper):
    """Records a video of the run"""
    FPS = 10

    def __init__(self, env: RLEnv, video_folder: str = None, video_encoding: Literal["mp4", "avi"]="mp4") -> None:
        super().__init__(env)
        if not video_folder:
            video_folder = "videos/"
        if not video_folder.endswith("/"):
            video_folder += "/"
        directory = os.path.dirname(video_folder)
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.video_folder = video_folder
        self.video_extension = video_encoding
        self._video_count = 0
        self._recorder = None
        match video_encoding:
            case "mp4": self._four_cc = cv2.VideoWriter_fourcc(*"mp4v")
            case "avi": self._four_cc = cv2.VideoWriter_fourcc(*"XVID")
            case other: raise ValueError(f"Unsupported file video encoding: {other}")
        

    def step(self, actions):
        obs, r, done, info = super().step(actions)
        self._recorder.write(self.render("rgb_array"))
        if done:
            self._recorder.release()
        return obs, r, done, info

    def reset(self):
        res = super().reset()
        image = self.render("rgb_array")
        height, width, _ = image.shape
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        video_name = os.path.join(self.video_folder, f"{self._video_count}-{timestamp}.{self.video_extension}")
        self._recorder = cv2.VideoWriter(video_name, self._four_cc, VideoRecorder.FPS, (width, height))
        self._recorder.write(image)
        self._video_count += 1
        return res

    def __del__(self):
        if self._recorder is not None:
            self._recorder.release()
