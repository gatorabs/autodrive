from src.application.configuration.system_initializer import SystemInitializer
from src.application.orchestration.process_manager import ProcessManager, ProcessTargets
from src.application.state import RuntimeControls, SharedFrames, UiControls


def create_initializer():
    from src.infrastructure.adapters.serial.serial_comm import SerialCommunicator
    from src.infrastructure.adapters.video.video_utility_process import detect_camera_indices
    from src.infrastructure.constants.colors_constants import RED, RESET
    from src.infrastructure.constants.path_constants import CALIBRATION_FILE, DEFAULT_UI_PATH
    from src.infrastructure.data.repository.calibration_repository import default_settings_store

    initializer = SystemInitializer(
        settings_store=default_settings_store,
        default_ui_path=DEFAULT_UI_PATH,
        camera_indices_detector=detect_camera_indices,
        serial_ports_lister=SerialCommunicator.list_available_ports,
        false_color=RED,
        reset_color=RESET,
    )
    return initializer, default_settings_store, CALIBRATION_FILE


def create_runtime_state(manager, user_flags):
    from src.infrastructure.constants.path_constants import CALIBRATION_FILE
    from src.infrastructure.data.repository.calibration_repository import default_settings_store

    initializer, _, _ = create_initializer()
    calibrated_data = default_settings_store.load(CALIBRATION_FILE)
    initial_tk = {**calibrated_data, **user_flags}

    shared_controls = RuntimeControls(manager.dict(initializer.init_shared_controls(user_flags)))
    tk_controls = UiControls(manager.dict(initial_tk))
    shared_frames = SharedFrames(manager.dict())

    return shared_controls, tk_controls, shared_frames, user_flags


def build_process_targets() -> ProcessTargets:
    from src.application.usecases.camera_capture_multiprocess import camera_capture_process
    from src.application.usecases.data_sender_multiprocess import data_sender_process
    from src.application.usecases.lane_detection_multiprocess import lane_detection_process
    from src.application.usecases.manual_mode_multiprocess import manual_video_process
    from src.application.usecases.object_detector_multiprocess import object_detection_process
    from src.infrastructure.adapters.detection.object_detection import ObjectDetector
    from src.infrastructure.adapters.serial.serial_comm import SerialCommunicator
    from src.infrastructure.adapters.video.video_manager_process import VideoSourceManager
    from src.presentation.api.web_server.app import start_flask_server
    from src.presentation.api.web_server.lifecycle import shutdown_flask_server
    from src.infrastructure.logging.logger import Logger
    from src.infrastructure.utils.priorities_processor import set_process_priority
    from src.presentation.lane_overlay_renderer import draw_overlays

    return ProcessTargets(
        sender=data_sender_process,
        camera=camera_capture_process,
        lane=lane_detection_process,
        object_detection=object_detection_process,
        manual_video=manual_video_process,
        web_server=start_flask_server,
        web_server_shutdown=shutdown_flask_server,
        lane_overlay_renderer=draw_overlays,
        logger_factory=Logger,
        priority_setter=set_process_priority,
        video_source_manager_factory=VideoSourceManager,
        serial_communicator_factory=SerialCommunicator,
        object_detector_factory=ObjectDetector,
    )


def build_process_manager(shared_controls, shared_frames, tk_controls, user_flags) -> ProcessManager:
    from src.infrastructure.constants.services_constants.process_constants import shutdown_endpoint
    from src.infrastructure.logging.logger import Logger

    return ProcessManager(
        shared_controls=shared_controls,
        shared_frames=shared_frames,
        tk_controls=tk_controls,
        user_flags=user_flags,
        targets=build_process_targets(),
        shutdown_url=shutdown_endpoint,
        logger=Logger("ProcessManager"),
    )


def terminate_runtime_processes(processes, manager_instance) -> None:
    from src.infrastructure.utils.process_utils import terminate_if_alive

    for process in processes:
        terminate_if_alive(process)

    for process in (
        manager_instance.flask_proc,
        manager_instance.lane_proc,
        manager_instance.object_proc,
        manager_instance.camera_proc,
    ):
        terminate_if_alive(process)
