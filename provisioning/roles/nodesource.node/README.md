# ansible-nodejs-role

This is an Ansible role which adds the the NodeSource APT repository and installs Node.js.

Currently this role supports the following operating systems and releases.

* **Ubuntu 12.04 LTS** (Precise Pangolin)
* **Ubuntu 14.04 LTS** (Trusty Tahr)

## Usage

Install the playbook via Ansible Galaxy:

```text
$ ansible-galaxy install nodesource.node
```

Then configure it as follows:

```yaml
- hosts: servers
  roles:
     - nodesource.node
```

## Role Variables

- `nodejs_nodesource_pin_priority`: Pin-Priority of the NodeSource repository (default: `500`).
- `nodejs_version`: Set Node version (options: `0.10` or `0.12` or `4.4`, default: `4.4`)

## Testing

To test this role using Docker:

```
$ docker build .
```

## Author

Mark Wolfe <mark@wolfe.id.au>

## License

This code is Copyright (c) 2014 NodeSource and Mark Wolfe and licenced under the MIT licence. All rights not explicitly granted in the MIT license are reserved. See the included [LICENSE.md](./LICENSE.md) file for more details.
