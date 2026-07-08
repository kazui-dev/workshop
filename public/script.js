document.addEventListener('DOMContentLoaded', () => {
    let stickX = 0;
    let stickY = 0;
    let intervalId = null;

    const idleJoystick = document.getElementById('idle-joystick');

    const manager = nipplejs.create({
        zone: document.getElementById('joystick-area'),
        mode: 'dynamic',
        catchDistance: 150,
        color: '#ffffff',
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
        console.log(JSON.stringify(pwmData));
    }

    manager.on('start', () => {
        if (idleJoystick && idleJoystick.style.opacity !== '0') {
            idleJoystick.style.opacity = '0';
        }

        stickX = 0;
        stickY = 0;
        
        if (intervalId) clearInterval(intervalId);
        intervalId = setInterval(sendDataInterval, 50);
    });

    manager.on('move', (evt, data) => {
        if (data && data.vector) {
            stickX = data.vector.x;
            stickY = data.vector.y;
        }
    });

    manager.on('end', () => {
        if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
        }
        
        stickX = 0;
        stickY = 0;
        
        console.log(JSON.stringify({ left: 0, right: 0 }));

        if (idleJoystick) {
            idleJoystick.style.opacity = '1';
        }
    });
});