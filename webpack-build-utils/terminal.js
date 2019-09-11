const { exec } = require('child_process');

function runInTerminal() {
    exec(process.argv[2], error => {
        if (error) {
            console.error(`exec error: ${error.toString()}`);
            return;
        }
        console.info(`stdout: Successfully executed ${process.argv[2]}`);
    });
}

runInTerminal();
