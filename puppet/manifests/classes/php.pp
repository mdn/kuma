# Ensure PHP is installed
class php {
    # TODO: Make sure PHP 5.2+ is installed
    package {
        [ "php", "php-cli", "php-common", "php-gd", "php-mbstring", "php-mysql" ]:
        ensure => installed;
    }
}
