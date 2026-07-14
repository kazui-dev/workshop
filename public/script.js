document.addEventListener('DOMContentLoaded', () => {
    let stickX = 0;
    let stickY = 0;
    let intervalId = null;
    let websocket = null;
    let reconnectTimeoutId = null;
    let inputActive = false;

    const idleJoystick = document.getElementById('idle-joystick');
    const videoStreamArea = document.getElementById('video-stream-area');
    const fullscreenButton = document.getElementById('fullscreen-button');
    const fullscreenIcon = document.getElementById('fullscreen-icon');
    const portraitMediaQuery = window.matchMedia('(orientation: portrait)');
    const websocketUrl = `ws://${location.hostname}:8765`;

    function isWebSocketConnected() {
        return websocket && websocket.readyState === WebSocket.OPEN;
    }

    function sendPWM(pwmData) {
        if (!isWebSocketConnected()) {
            return;
        }

        try {
            websocket.send(JSON.stringify(pwmData));
        } catch (error) {
            console.error('Failed to send PWM data:', error);
        }
    }

    function scheduleReconnect() {
        if (reconnectTimeoutId) {
            return;
        }

        reconnectTimeoutId = setTimeout(() => {
            reconnectTimeoutId = null;
            connectWebSocket();
        }, 1000);
    }

    function connectWebSocket() {
        if (
            websocket
            && (
                websocket.readyState === WebSocket.OPEN
                || websocket.readyState === WebSocket.CONNECTING
            )
        ) {
            return;
        }

        try {
            websocket = new WebSocket(websocketUrl);
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            scheduleReconnect();
            return;
        }

        websocket.addEventListener('open', () => {
            console.info('WebSocket connected');
        });

        websocket.addEventListener('error', (event) => {
            console.error('WebSocket error:', event);
        });

        websocket.addEventListener('close', () => {
            websocket = null;
            scheduleReconnect();
        });
    }

    const manager = nipplejs.create({
        zone: document.getElementById('joystick-area'),
        mode: 'dynamic',
        catchDistance: 150,
        color: {
            back: 'rgba(255, 255, 255, 0.2)',
            front: '#ffffff'
        },
        size: 100
    });

    function calculatePWM(x, y) {
        const forward = y;
        const turn = x;

        let leftPWM = forward + turn;
        let rightPWM = forward - turn;

        leftPWM = Math.max(-1.0, Math.min(1.0, leftPWM));
        rightPWM = Math.max(-1.0, Math.min(1.0, rightPWM));

        return {
            left: Math.round(leftPWM * 255),
            right: Math.round(rightPWM * 255)
        };
    }

    function sendDataInterval() {
        const pwmData = calculatePWM(stickX, stickY);
        sendPWM(pwmData);
    }

    function stopJoystickInput() {
        if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
        }

        inputActive = false;
        stickX = 0;
        stickY = 0;
        sendPWM({ left: 0, right: 0 });

        if (idleJoystick) {
            idleJoystick.style.opacity = '1';
        }
    }

    manager.on('start', () => {
        if (idleJoystick && idleJoystick.style.opacity !== '0') {
            idleJoystick.style.opacity = '0';
        }

        stickX = 0;
        stickY = 0;
        inputActive = true;
        
        if (intervalId) clearInterval(intervalId);
        intervalId = setInterval(sendDataInterval, 50);
    });

    manager.on('move', (evt) => {
        if (!inputActive) {
            return;
        }

        const data = evt.data;
        if (data && data.vector) {
            stickX = data.vector.x;
            stickY = data.vector.y;
        }
    });

    manager.on('end', () => {
        stopJoystickInput();
    });

    if (portraitMediaQuery.addEventListener) {
        portraitMediaQuery.addEventListener('change', stopJoystickInput);
    } else {
        portraitMediaQuery.addListener(stopJoystickInput);
    }

    function getFullscreenElement() {
        return document.fullscreenElement || document.webkitFullscreenElement;
    }

    function getRequestFullscreen() {
        return videoStreamArea.requestFullscreen || videoStreamArea.webkitRequestFullscreen;
    }

    function getExitFullscreen() {
        return document.exitFullscreen || document.webkitExitFullscreen;
    }

    function isFullscreenSupported() {
        const fullscreenEnabled = (
            document.fullscreenEnabled ?? document.webkitFullscreenEnabled
        );

        return Boolean(
            getRequestFullscreen()
            && getExitFullscreen()
            && fullscreenEnabled !== false
        );
    }

    function updateFullscreenButton() {
        const isFullscreen = getFullscreenElement() === videoStreamArea;
        fullscreenButton.setAttribute(
            'aria-label',
            isFullscreen ? '全画面表示を終了' : 'カメラ映像を全画面表示'
        );
        fullscreenButton.setAttribute('aria-pressed', String(isFullscreen));
        fullscreenIcon.src = isFullscreen
            ? 'assets/fullscreen-exit.svg'
            : 'assets/fullscreen.svg';
    }

    async function toggleFullscreen() {
        try {
            if (getFullscreenElement()) {
                await getExitFullscreen().call(document);
                return;
            }

            await getRequestFullscreen().call(videoStreamArea);
        } catch (error) {
            console.error('Failed to toggle fullscreen:', error);
        }
    }

    if (isFullscreenSupported()) {
        fullscreenButton.hidden = false;
        fullscreenButton.addEventListener('click', toggleFullscreen);
        document.addEventListener('fullscreenchange', updateFullscreenButton);
        document.addEventListener('webkitfullscreenchange', updateFullscreenButton);
    }

    connectWebSocket();
});
