/** This is purely for local development. It's a fake/mock Google Analytics
 * server endpoint.
 * It's not strictly working as Google Analytics does but enough to foreground
 * log the collect POSTs coming in.
 *
 * See the README.md for tips on how this works and to do development on it.
 */
const express = require('express');
const chalk = require('chalk');

const app = express();
const port = parseInt(process.env.PORT || '7777');

app.get('/', (req, res) => res.send('Hello World!'));

app.post('/collect', (req, res) => {
    const requiredKeys = ['v', 'tid', 'cid', 'ec', 'ea', 'el'];
    for (let key of requiredKeys) {
        if (!(key in req.query)) {
            return res.status(400).send(`Missing query key '${key}'`);
        }
    }
    const { ec, ea, el, cid } = req.query;
    function showValue(s, maxLength) {
        if (s.length > maxLength) {
            return s.slice(0, maxLength - 1) + '…';
        }
        return s;
    }
    const parts = [
        chalk.bold('ec: ') + chalk.green(showValue(ec, 20)),
        chalk.bold('ea: ') + chalk.green(showValue(ea, 30)),
        chalk.bold('el: ') + chalk.green(showValue(el, 50)),
    ];
    const output = `[${new Date().toISOString()}] GA TRACK EVENT cid=${showValue(
        cid,
        10
    )} | ${parts.join(', ')}`;
    console.log(output);
    res.status(201).send(`${output}\n`);
});
app.listen(port, () => console.log(`Mockga app listening on port ${port}!`));
