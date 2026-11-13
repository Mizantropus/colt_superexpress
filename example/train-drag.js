const viewport = document.querySelector(".background_wrapper");
const track = document.querySelector(".mover_wrapper");
const mover = document.querySelector(".mover");
const train = document.querySelector(".train_wrapper");
const shootButton = document.querySelector("#shoot");
const shooter = document.querySelector(".cowboy_red.staying_right");
const shootFromHipButton = document.querySelector("#shoot_from_hip");
const hipShooter = document.querySelector(".cowboy_red.staying_left");
const rideButton = document.querySelector("#ride");
const hobbyHorse = document.querySelector(".hobby_horsing");
const shootItselfButton = document.querySelector("#shoot_itself");
const selfShooter = document.querySelector(".cowboy_red:not(.staying_left):not(.staying_right)");
const climbingButton = document.querySelector("#climbing");
const climber = document.querySelector(".cowboy_red.climber");
const fallButton = document.querySelector("#fall_forvard");
const fallingCowboy = document.querySelector(".cowboy_red.fall_target");
const fallBackButton = document.querySelector("#fall_back");
const fallingBackwardCowboy = document.querySelector(".cowboy_red.fall_back_target");
const gettingUpButton = document.querySelector("#gettingup");
const gettingUpCowboy = document.querySelector(".cowboy_red.getup_target");
const rotateButton = document.querySelector("#rotate");
const rotatingCowboy = document.querySelector(".cowboy_red.rotate_target");
const musicAudio = document.querySelector("#music_audio");
const musicToggle = document.querySelector("#music_toggle");
const musicVolume = document.querySelector("#music_volume");

if (viewport && track && mover && train) {
  let progress = 0.5;
  let dragOffset = 0;
  let dragging = false;

  function updatePositions() {
    const trackWidth = track.clientWidth;
    const moverRadius = mover.offsetWidth / 2;
    const minCenter = Math.min(moverRadius, trackWidth / 2);
    const maxCenter = Math.max(minCenter, trackWidth - moverRadius);
    const center = minCenter + (maxCenter - minCenter) * progress;
    const trainOffset = (viewport.clientWidth - train.offsetWidth) * progress;

    mover.style.left = `${center}px`;
    train.style.left = `${trainOffset}px`;
    mover.setAttribute("aria-valuenow", String(Math.round(progress * 100)));
  }

  function setProgressFromPointer(clientX) {
    const trackLeft = track.getBoundingClientRect().left;
    const trackWidth = track.clientWidth;
    const moverRadius = mover.offsetWidth / 2;
    const minCenter = Math.min(moverRadius, trackWidth / 2);
    const maxCenter = Math.max(minCenter, trackWidth - moverRadius);
    const center = Math.min(
      maxCenter,
      Math.max(minCenter, clientX - trackLeft - dragOffset),
    );

    progress = maxCenter === minCenter ? 0.5 : (center - minCenter) / (maxCenter - minCenter);
    updatePositions();
  }

  if (musicAudio && musicToggle && musicVolume) {
    const playlist = ["1.mp3", "2.mp3"];
    let trackIndex = 0;
    let muted = false;
    let lastVolume = 0.2;

    musicAudio.volume = 0.2;
    musicAudio.src = playlist[trackIndex];

    function updateMusicControls() {
      musicAudio.muted = muted;
      musicToggle.dataset.muted = String(muted);
      musicToggle.setAttribute("aria-pressed", String(muted));
      musicToggle.setAttribute("aria-label", muted ? "Включить звук" : "Отключить звук");
      musicVolume.value = String(Math.round(musicAudio.volume * 100));
    }

    function startPlayback() {
      musicAudio.play().catch((error) => {
        if (error.name === "NotAllowedError") {
          window.addEventListener("pointerdown", startAfterInteraction, { once: true });
          window.addEventListener("keydown", startAfterInteraction, { once: true });
          return;
        }

        console.error("Не удалось воспроизвести музыку:", error);
      });
    }

    function startAfterInteraction() {
      window.removeEventListener("pointerdown", startAfterInteraction);
      window.removeEventListener("keydown", startAfterInteraction);
      startPlayback();
    }

    musicAudio.addEventListener("ended", () => {
      trackIndex = (trackIndex + 1) % playlist.length;
      musicAudio.src = playlist[trackIndex];
      startPlayback();
    });

    musicAudio.addEventListener("error", () => {
      console.error("Не удалось загрузить аудиофайл:", musicAudio.currentSrc);
    });

    musicToggle.addEventListener("click", () => {
      if (muted) {
        muted = false;
        musicAudio.volume = lastVolume;
      } else {
        if (musicAudio.volume > 0) {
          lastVolume = musicAudio.volume;
        }
        muted = true;
        musicAudio.volume = 0;
      }

      updateMusicControls();
      if (!musicAudio.paused && !muted) {
        return;
      }
      if (!muted && musicAudio.paused) {
        startPlayback();
      }
    });

    musicVolume.addEventListener("input", () => {
      const volume = Number(musicVolume.value) / 100;
      musicAudio.volume = volume;
      muted = volume === 0;
      if (volume > 0) {
        lastVolume = volume;
      }

      updateMusicControls();
      if (!muted && musicAudio.paused) {
        startPlayback();
      }
    });

    updateMusicControls();
    startPlayback();
  }

  if (rideButton && hobbyHorse) {
    rideButton.addEventListener("click", () => {
      if (hobbyHorse.classList.contains("horse")) {
        return;
      }

      hobbyHorse.classList.add("horse");
      rideButton.disabled = true;
    });

    hobbyHorse.addEventListener("animationend", (event) => {
      if (event.animationName !== "horse-ride") {
        return;
      }

      hobbyHorse.classList.remove("horse");
      rideButton.disabled = false;
    });
  }

  if (shootButton && shooter) {
    shootButton.addEventListener("click", () => {
      if (shooter.classList.contains("shoot_right")) {
        return;
      }

      shooter.classList.add("shoot_right");
      shootButton.disabled = true;
    });

    shooter.addEventListener("animationend", (event) => {
      if (event.animationName !== "cowboy-shoot") {
        return;
      }

      shooter.classList.remove("shoot_right");
      shootButton.disabled = false;
    });
  }

  if (shootFromHipButton && hipShooter) {
    shootFromHipButton.addEventListener("click", () => {
      if (hipShooter.classList.contains("cowboy_shoot_from_hip")) {
        return;
      }

      hipShooter.classList.add("cowboy_shoot_from_hip");
      shootFromHipButton.disabled = true;
    });

    hipShooter.addEventListener("animationend", (event) => {
      if (event.animationName !== "cowboy-shoot-from-hip") {
        return;
      }

      hipShooter.classList.remove("cowboy_shoot_from_hip");
      shootFromHipButton.disabled = false;
    });
  }

  if (climbingButton && climber) {
    climbingButton.addEventListener("click", () => {
      if (climber.classList.contains("climbing")) {
        return;
      }

      if (climber.classList.contains("climbing_up")) {
        climber.classList.remove("climbing_up");
        return;
      }

      climber.classList.add("climbing");
      climbingButton.disabled = true;
    });

    climber.addEventListener("animationend", (event) => {
      if (event.animationName !== "cowboy-climbing") {
        return;
      }

      climber.classList.remove("climbing");
      climber.classList.add("climbing_up");
      climbingButton.disabled = false;
    });
  }

  if (fallButton && fallingCowboy) {
    fallButton.addEventListener("click", () => {
      if (fallingCowboy.classList.contains("fall_forvard")) {
        return;
      }

      if (fallingCowboy.classList.contains("laying_right")) {
        fallingCowboy.classList.remove("laying_right");
        return;
      }

      fallingCowboy.classList.add("fall_forvard");
      fallButton.disabled = true;
    });

    fallingCowboy.addEventListener("animationend", (event) => {
      if (event.target !== fallingCowboy || event.animationName !== "cowboy-fall-move") {
        return;
      }

      fallingCowboy.classList.remove("fall_forvard");
      fallingCowboy.classList.add("laying_right");
      fallButton.disabled = false;
    });
  }

  if (fallBackButton && fallingBackwardCowboy) {
    fallBackButton.addEventListener("click", () => {
      if (fallingBackwardCowboy.classList.contains("fall_back")) {
        return;
      }

      if (fallingBackwardCowboy.classList.contains("laying_right")) {
        fallingBackwardCowboy.classList.remove("laying_right");
        return;
      }

      fallingBackwardCowboy.classList.add("fall_back");
      fallBackButton.disabled = true;
    });

    fallingBackwardCowboy.addEventListener("animationend", (event) => {
      if (event.target !== fallingBackwardCowboy || event.animationName !== "cowboy-fall-back-move") {
        return;
      }

      fallingBackwardCowboy.classList.remove("fall_back");
      fallingBackwardCowboy.classList.add("laying_right");
      fallBackButton.disabled = false;
    });
  }

  if (gettingUpButton && gettingUpCowboy) {
    gettingUpButton.addEventListener("click", () => {
      if (gettingUpCowboy.classList.contains("getup_right")) {
        return;
      }

      if (gettingUpCowboy.classList.contains("laying_right")) {
        gettingUpCowboy.classList.add("getup_right");
        gettingUpButton.disabled = true;
        return;
      }

      gettingUpCowboy.classList.add("laying_right");
    });

    gettingUpCowboy.addEventListener("animationend", (event) => {
      if (event.target !== gettingUpCowboy || event.animationName !== "cowboy-getup-right") {
        return;
      }

      gettingUpCowboy.classList.remove("getup_right", "laying_right");
      gettingUpButton.disabled = false;
    });
  }

  if (rotateButton && rotatingCowboy) {
    rotateButton.addEventListener("click", () => {
      if (rotatingCowboy.classList.contains("cowboy_rotate")) {
        return;
      }

      if (rotatingCowboy.classList.contains("staying_left")) {
        rotatingCowboy.classList.remove("staying_left");
        return;
      }

      rotatingCowboy.classList.add("cowboy_rotate");
      rotateButton.disabled = true;
    });

    rotatingCowboy.addEventListener("animationend", (event) => {
      if (event.target !== rotatingCowboy || event.animationName !== "cowboy-rotate") {
        return;
      }

      rotatingCowboy.classList.remove("cowboy_rotate");
      rotatingCowboy.classList.add("staying_left");
      rotateButton.disabled = false;
    });
  }

  if (shootItselfButton && selfShooter) {
    shootItselfButton.addEventListener("click", () => {
      if (selfShooter.classList.contains("laying_right")) {
        selfShooter.classList.remove("laying_right");
        return;
      }

      if (selfShooter.classList.contains("shoot_right") || selfShooter.classList.contains("shoot_left")) {
        return;
      }

      selfShooter.classList.add("shoot_right", "cowboy_shoot_itself");
      shootItselfButton.disabled = true;
    });

    selfShooter.addEventListener("animationend", (event) => {
      if (event.target !== selfShooter || event.animationName !== "cowboy-shoot-itself") {
        return;
      }

      selfShooter.classList.remove("shoot_right", "cowboy_shoot_itself");
      selfShooter.classList.add("laying_right");
      shootItselfButton.disabled = false;
    });
  }

  mover.addEventListener("pointerdown", (event) => {
    dragging = true;
    dragOffset = event.clientX - mover.getBoundingClientRect().left - mover.offsetWidth / 2;
    mover.setPointerCapture(event.pointerId);
    event.preventDefault();
  });

  mover.addEventListener("pointermove", (event) => {
    if (dragging) {
      setProgressFromPointer(event.clientX);
    }
  });

  function stopDragging() {
    dragging = false;
  }

  mover.addEventListener("pointerup", stopDragging);
  mover.addEventListener("pointercancel", stopDragging);

  mover.addEventListener("keydown", (event) => {
    let nextProgress = progress;

    if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
      nextProgress -= 0.02;
    } else if (event.key === "ArrowRight" || event.key === "ArrowUp") {
      nextProgress += 0.02;
    } else if (event.key === "PageDown") {
      nextProgress -= 0.1;
    } else if (event.key === "PageUp") {
      nextProgress += 0.1;
    } else if (event.key === "Home") {
      nextProgress = 0;
    } else if (event.key === "End") {
      nextProgress = 1;
    } else {
      return;
    }

    event.preventDefault();
    progress = Math.min(1, Math.max(0, nextProgress));
    updatePositions();
  });

  window.addEventListener("resize", updatePositions);
  updatePositions();
}
