const MAX_PWM = 255;
const PWM_SEND_INTERVAL_MS = 50;
const WEBSOCKET_RECONNECT_DELAY_MS = 1000;
const STOP_PWM = Object.freeze({ left: 0, right: 0 });

function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

function calculatePWM(x, y) {
    const left = clamp(y + x, -1, 1);
    const right = clamp(y - x, -1, 1);

    return {
        left: Math.round(left * MAX_PWM),
        right: Math.round(right * MAX_PWM)
    };
}

function createWebSocketClient(url) {
    let socket = null;
    let reconnectTimeoutId = null;

    function scheduleReconnect() {
        if (reconnectTimeoutId !== null) {
            return;
        }

        reconnectTimeoutId = setTimeout(() => {
            reconnectTimeoutId = null;
            connect();
        }, WEBSOCKET_RECONNECT_DELAY_MS);
    }

    function connect() {
        const connectionInProgress = socket && (
            socket.readyState === WebSocket.OPEN
            || socket.readyState === WebSocket.CONNECTING
        );

        if (connectionInProgress) {
            return;
        }

        let connection;

        try {
            connection = new WebSocket(url);
            socket = connection;
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            scheduleReconnect();
            return;
        }

        connection.addEventListener('open', () => {
            console.info('WebSocket connected');
        });

        connection.addEventListener('error', (event) => {
            console.error('WebSocket error:', event);
        });

        connection.addEventListener('close', () => {
            if (socket === connection) {
                socket = null;
            }
            scheduleReconnect();
        });
    }

    function send(data) {
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            return;
        }

        try {
            socket.send(JSON.stringify(data));
        } catch (error) {
            console.error('Failed to send PWM data:', error);
        }
    }

    connect();

    return { send };
}

function setupJoystick(zone, idleJoystick, sendPWM) {
    const state = {
        x: 0,
        y: 0,
        active: false,
        intervalId: null
    };

    const manager = nipplejs.create({
        zone,
        mode: 'dynamic',
        catchDistance: 150,
        color: {
            back: 'rgba(255, 255, 255, 0.2)',
            front: '#ffffff'
        },
        size: 100
    });

    function stop() {
        if (state.intervalId !== null) {
            clearInterval(state.intervalId);
            state.intervalId = null;
        }

        state.active = false;
        state.x = 0;
        state.y = 0;
        idleJoystick.classList.remove('is-input-active');
        sendPWM(STOP_PWM);
    }

    manager.on('start', () => {
        if (state.intervalId !== null) {
            clearInterval(state.intervalId);
        }

        state.active = true;
        state.x = 0;
        state.y = 0;
        idleJoystick.classList.add('is-input-active');
        state.intervalId = setInterval(() => {
            sendPWM(calculatePWM(state.x, state.y));
        }, PWM_SEND_INTERVAL_MS);
    });

    manager.on('move', (event) => {
        const vector = event.data?.vector;

        if (!state.active || !vector) {
            return;
        }

        state.x = vector.x;
        state.y = vector.y;
    });

    manager.on('end', stop);

    return { stop };
}

function setupFullscreen(area, button, icon) {
    const supported = Boolean(
        document.fullscreenEnabled
        && typeof area.requestFullscreen === 'function'
        && typeof document.exitFullscreen === 'function'
    );

    if (!supported) {
        return;
    }

    async function syncOrientation(active) {
        const orientation = window.screen.orientation;

        if (!orientation) {
            return;
        }

        try {
            if (active && typeof orientation.lock === 'function') {
                await orientation.lock('landscape');
            } else if (!active && typeof orientation.unlock === 'function') {
                orientation.unlock();
            }
        } catch (error) {
            console.warn('Failed to update screen orientation:', error);
        }
    }

    function handleFullscreenChange() {
        const active = document.fullscreenElement === area;

        button.setAttribute(
            'aria-label',
            active ? '全画面表示を終了' : 'カメラ映像を全画面表示'
        );
        button.setAttribute('aria-pressed', String(active));
        icon.src = active
            ? 'assets/fullscreen-exit.svg'
            : 'assets/fullscreen.svg';
        void syncOrientation(active);
    }

    async function toggle() {
        button.disabled = true;

        try {
            if (document.fullscreenElement === area) {
                await document.exitFullscreen();
            } else {
                await area.requestFullscreen();
            }
        } catch (error) {
            console.error('Failed to toggle fullscreen:', error);
        } finally {
            button.disabled = false;
        }
    }

    button.hidden = false;
    button.addEventListener('click', toggle);
    document.addEventListener('fullscreenchange', handleFullscreenChange);
}

document.addEventListener('DOMContentLoaded', () => {
    const idleJoystick = document.getElementById('idle-joystick');
    const joystickArea = document.getElementById('joystick-area');
    const videoStreamArea = document.getElementById('video-stream-area');
    const fullscreenButton = document.getElementById('fullscreen-button');
    const fullscreenIcon = document.getElementById('fullscreen-icon');

    const websocketClient = createWebSocketClient(
        `ws://${location.hostname}:8765`
    );
    const joystick = setupJoystick(
        joystickArea,
        idleJoystick,
        websocketClient.send
    );

    window.matchMedia('(orientation: portrait)')
        .addEventListener('change', joystick.stop);

    setupFullscreen(videoStreamArea, fullscreenButton, fullscreenIcon);
});
