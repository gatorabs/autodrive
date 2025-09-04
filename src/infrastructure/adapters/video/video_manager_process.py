import time
from src.infrastructure.adapters.video.video_process import VideoProcessor


class VideoSourceManager:
    def __init__(self, current_source=None):
        self._warn_unavailable = False
        self._last_retry = 0.0
        self._current_source = current_source

    @property
    def current_source(self):
        return self._current_source

    def open_video_source(
        self,
        lane_queue,
        shared_controls,
        logger,
        safe_stop_cb,
        cooldown: float = 2.0,
    ):
        now = time.monotonic()
        if self._warn_unavailable and (now - self._last_retry) < cooldown:
            return None

        try:
            video_proc = VideoProcessor(video_source=self._current_source)
            logger.info(f"Fonte aberta: {self._current_source}")
            self._warn_unavailable = False
            self._last_retry = 0.0
            return video_proc
        except Exception as e:  # pragma: no cover - defensive
            if not self._warn_unavailable:
                logger.error(f"Falha ao abrir fonte {self._current_source}: {e}")
                safe_stop_cb(lane_queue, shared_controls, logger, reason=str(e))
                self._warn_unavailable = True
            self._last_retry = now
            return None

    def ensure_video_source(
        self,
        video_processor,
        requested_source,
        queue,
        shared_controls,
        logger,
        safe_stop_cb,
        cooldown: float = 2.0,
    ):
        desired_source = (
            requested_source if requested_source is not None else self._current_source
        )

        if desired_source is None:
            logger.error("Nenhuma fonte definida para abrir/trocar.")
            safe_stop_cb(queue, shared_controls, logger, reason="Fonte não definida")
            return None, self._current_source

        if video_processor is None or not video_processor.is_frame_open():
            self._current_source = desired_source
            vp = self.open_video_source(
                lane_queue=queue,
                shared_controls=shared_controls,
                logger=logger,
                safe_stop_cb=safe_stop_cb,
                cooldown=cooldown,
            )
            return (vp, self._current_source) if vp is not None else (None, self._current_source)

        if desired_source != self._current_source:
            now = time.monotonic()
            if self._warn_unavailable and (now - self._last_retry) < cooldown:
                return video_processor, self._current_source

            try:
                new_vp = VideoProcessor(video_source=desired_source)
                logger.info(
                    f"Trocando Source de {self._current_source} para {desired_source}"
                )
                self._warn_unavailable = False
                self._last_retry = 0.0
            except Exception as e:
                if not self._warn_unavailable:
                    logger.error(f"Falha ao trocar para fonte {desired_source}: {e}")
                self._warn_unavailable = True
                self._last_retry = now

                if video_processor.is_frame_open():
                    return video_processor, self._current_source

                safe_stop_cb(queue, shared_controls, logger, reason=str(e))
                return None, self._current_source

            try:
                video_processor.release()
            except Exception:
                pass
            self._current_source = desired_source
            return new_vp, self._current_source

        return video_processor, self._current_source

    def switch_source(self, video_processor, new_source, logger):
        if new_source != self._current_source:
            logger.info(f"Trocando Source de {self._current_source} para {new_source}")
            try:
                new_video = VideoProcessor(video_source=new_source)
            except Exception as e:
                logger.error(f"Falha ao trocar para fonte {new_source}: {e}")
                return video_processor
            if video_processor:
                video_processor.release()
            self._current_source = new_source
            return new_video
        return video_processor
