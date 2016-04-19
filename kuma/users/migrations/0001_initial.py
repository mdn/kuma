# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import django.contrib.auth.models
import django.utils.timezone
from django.conf import settings
import django.core.validators
import kuma.core.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, max_length=30, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.', 'invalid')], help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True, verbose_name='username')),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('email', models.EmailField(max_length=254, verbose_name='email address', blank=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('timezone', models.CharField(default=b'US/Pacific', max_length=42, verbose_name='Timezone', blank=True, choices=[('Africa', [('Africa/Abidjan', 'Abidjan (GMT+0000)'), ('Africa/Accra', 'Accra (GMT+0000)'), ('Africa/Addis_Ababa', 'Addis Ababa (GMT+0300)'), ('Africa/Algiers', 'Algiers (GMT+0100)'), ('Africa/Asmara', 'Asmara (GMT+0300)'), ('Africa/Bamako', 'Bamako (GMT+0000)'), ('Africa/Bangui', 'Bangui (GMT+0100)'), ('Africa/Banjul', 'Banjul (GMT+0000)'), ('Africa/Bissau', 'Bissau (GMT+0000)'), ('Africa/Blantyre', 'Blantyre (GMT+0200)'), ('Africa/Brazzaville', 'Brazzaville (GMT+0100)'), ('Africa/Bujumbura', 'Bujumbura (GMT+0200)'), ('Africa/Cairo', 'Cairo (GMT+0200)'), ('Africa/Casablanca', 'Casablanca (GMT+0000)'), ('Africa/Ceuta', 'Ceuta (GMT+0100)'), ('Africa/Conakry', 'Conakry (GMT+0000)'), ('Africa/Dakar', 'Dakar (GMT+0000)'), ('Africa/Dar_es_Salaam', 'Dar es Salaam (GMT+0300)'), ('Africa/Djibouti', 'Djibouti (GMT+0300)'), ('Africa/Douala', 'Douala (GMT+0100)'), ('Africa/El_Aaiun', 'El Aaiun (GMT+0000)'), ('Africa/Freetown', 'Freetown (GMT+0000)'), ('Africa/Gaborone', 'Gaborone (GMT+0200)'), ('Africa/Harare', 'Harare (GMT+0200)'), ('Africa/Johannesburg', 'Johannesburg (GMT+0200)'), ('Africa/Juba', 'Juba (GMT+0300)'), ('Africa/Kampala', 'Kampala (GMT+0300)'), ('Africa/Khartoum', 'Khartoum (GMT+0300)'), ('Africa/Kigali', 'Kigali (GMT+0200)'), ('Africa/Kinshasa', 'Kinshasa (GMT+0100)'), ('Africa/Lagos', 'Lagos (GMT+0100)'), ('Africa/Libreville', 'Libreville (GMT+0100)'), ('Africa/Lome', 'Lome (GMT+0000)'), ('Africa/Luanda', 'Luanda (GMT+0100)'), ('Africa/Lubumbashi', 'Lubumbashi (GMT+0200)'), ('Africa/Lusaka', 'Lusaka (GMT+0200)'), ('Africa/Malabo', 'Malabo (GMT+0100)'), ('Africa/Maputo', 'Maputo (GMT+0200)'), ('Africa/Maseru', 'Maseru (GMT+0200)'), ('Africa/Mbabane', 'Mbabane (GMT+0200)'), ('Africa/Mogadishu', 'Mogadishu (GMT+0300)'), ('Africa/Monrovia', 'Monrovia (GMT+0000)'), ('Africa/Nairobi', 'Nairobi (GMT+0300)'), ('Africa/Ndjamena', 'Ndjamena (GMT+0100)'), ('Africa/Niamey', 'Niamey (GMT+0100)'), ('Africa/Nouakchott', 'Nouakchott (GMT+0000)'), ('Africa/Ouagadougou', 'Ouagadougou (GMT+0000)'), ('Africa/Porto-Novo', 'Porto-Novo (GMT+0100)'), ('Africa/Sao_Tome', 'Sao Tome (GMT+0000)'), ('Africa/Tripoli', 'Tripoli (GMT+0200)'), ('Africa/Tunis', 'Tunis (GMT+0100)'), ('Africa/Windhoek', 'Windhoek (GMT+0200)')]), ('America', [('America/Adak', 'Adak (GMT-1000)'), ('America/Anchorage', 'Anchorage (GMT-0900)'), ('America/Anguilla', 'Anguilla (GMT-0400)'), ('America/Antigua', 'Antigua (GMT-0400)'), ('America/Araguaina', 'Araguaina (GMT-0300)'), ('America/Argentina/Buenos_Aires', 'Buenos Aires (GMT-0300)'), ('America/Argentina/Catamarca', 'Catamarca (GMT-0300)'), ('America/Argentina/Cordoba', 'Cordoba (GMT-0300)'), ('America/Argentina/Jujuy', 'Jujuy (GMT-0300)'), ('America/Argentina/La_Rioja', 'La Rioja (GMT-0300)'), ('America/Argentina/Mendoza', 'Mendoza (GMT-0300)'), ('America/Argentina/Rio_Gallegos', 'Rio Gallegos (GMT-0300)'), ('America/Argentina/Salta', 'Salta (GMT-0300)'), ('America/Argentina/San_Juan', 'San Juan (GMT-0300)'), ('America/Argentina/San_Luis', 'San Luis (GMT-0300)'), ('America/Argentina/Tucuman', 'Tucuman (GMT-0300)'), ('America/Argentina/Ushuaia', 'Ushuaia (GMT-0300)'), ('America/Aruba', 'Aruba (GMT-0400)'), ('America/Asuncion', 'Asuncion (GMT-0300)'), ('America/Atikokan', 'Atikokan (GMT-0500)'), ('America/Bahia', 'Bahia (GMT-0300)'), ('America/Bahia_Banderas', 'Bahia Banderas (GMT-0600)'), ('America/Barbados', 'Barbados (GMT-0400)'), ('America/Belem', 'Belem (GMT-0300)'), ('America/Belize', 'Belize (GMT-0600)'), ('America/Blanc-Sablon', 'Blanc-Sablon (GMT-0400)'), ('America/Boa_Vista', 'Boa Vista (GMT-0400)'), ('America/Bogota', 'Bogota (GMT-0500)'), ('America/Boise', 'Boise (GMT-0700)'), ('America/Cambridge_Bay', 'Cambridge Bay (GMT-0700)'), ('America/Campo_Grande', 'Campo Grande (GMT-0300)'), ('America/Cancun', 'Cancun (GMT-0500)'), ('America/Caracas', 'Caracas (GMT-0430)'), ('America/Cayenne', 'Cayenne (GMT-0300)'), ('America/Cayman', 'Cayman (GMT-0500)'), ('America/Chicago', 'Chicago (GMT-0600)'), ('America/Chihuahua', 'Chihuahua (GMT-0700)'), ('America/Costa_Rica', 'Costa Rica (GMT-0600)'), ('America/Creston', 'Creston (GMT-0700)'), ('America/Cuiaba', 'Cuiaba (GMT-0300)'), ('America/Curacao', 'Curacao (GMT-0400)'), ('America/Danmarkshavn', 'Danmarkshavn (GMT+0000)'), ('America/Dawson', 'Dawson (GMT-0800)'), ('America/Dawson_Creek', 'Dawson Creek (GMT-0700)'), ('America/Denver', 'Denver (GMT-0700)'), ('America/Detroit', 'Detroit (GMT-0500)'), ('America/Dominica', 'Dominica (GMT-0400)'), ('America/Edmonton', 'Edmonton (GMT-0700)'), ('America/Eirunepe', 'Eirunepe (GMT-0500)'), ('America/El_Salvador', 'El Salvador (GMT-0600)'), ('America/Fort_Nelson', 'Fort Nelson (GMT-0700)'), ('America/Fortaleza', 'Fortaleza (GMT-0300)'), ('America/Glace_Bay', 'Glace Bay (GMT-0400)'), ('America/Godthab', 'Godthab (GMT-0300)'), ('America/Goose_Bay', 'Goose Bay (GMT-0400)'), ('America/Grand_Turk', 'Grand Turk (GMT-0400)'), ('America/Grenada', 'Grenada (GMT-0400)'), ('America/Guadeloupe', 'Guadeloupe (GMT-0400)'), ('America/Guatemala', 'Guatemala (GMT-0600)'), ('America/Guayaquil', 'Guayaquil (GMT-0500)'), ('America/Guyana', 'Guyana (GMT-0400)'), ('America/Halifax', 'Halifax (GMT-0400)'), ('America/Havana', 'Havana (GMT-0500)'), ('America/Hermosillo', 'Hermosillo (GMT-0700)'), ('America/Indiana/Indianapolis', 'Indianapolis (GMT-0500)'), ('America/Indiana/Knox', 'Knox (GMT-0600)'), ('America/Indiana/Marengo', 'Marengo (GMT-0500)'), ('America/Indiana/Petersburg', 'Petersburg (GMT-0500)'), ('America/Indiana/Tell_City', 'Tell City (GMT-0600)'), ('America/Indiana/Vevay', 'Vevay (GMT-0500)'), ('America/Indiana/Vincennes', 'Vincennes (GMT-0500)'), ('America/Indiana/Winamac', 'Winamac (GMT-0500)'), ('America/Inuvik', 'Inuvik (GMT-0700)'), ('America/Iqaluit', 'Iqaluit (GMT-0500)'), ('America/Jamaica', 'Jamaica (GMT-0500)'), ('America/Juneau', 'Juneau (GMT-0900)'), ('America/Kentucky/Louisville', 'Louisville (GMT-0500)'), ('America/Kentucky/Monticello', 'Monticello (GMT-0500)'), ('America/Kralendijk', 'Kralendijk (GMT-0400)'), ('America/La_Paz', 'La Paz (GMT-0400)'), ('America/Lima', 'Lima (GMT-0500)'), ('America/Los_Angeles', 'Los Angeles (GMT-0800)'), ('America/Lower_Princes', 'Lower Princes (GMT-0400)'), ('America/Maceio', 'Maceio (GMT-0300)'), ('America/Managua', 'Managua (GMT-0600)'), ('America/Manaus', 'Manaus (GMT-0400)'), ('America/Marigot', 'Marigot (GMT-0400)'), ('America/Martinique', 'Martinique (GMT-0400)'), ('America/Matamoros', 'Matamoros (GMT-0600)'), ('America/Mazatlan', 'Mazatlan (GMT-0700)'), ('America/Menominee', 'Menominee (GMT-0600)'), ('America/Merida', 'Merida (GMT-0600)'), ('America/Metlakatla', 'Metlakatla (GMT-0800)'), ('America/Mexico_City', 'Mexico City (GMT-0600)'), ('America/Miquelon', 'Miquelon (GMT-0300)'), ('America/Moncton', 'Moncton (GMT-0400)'), ('America/Monterrey', 'Monterrey (GMT-0600)'), ('America/Montevideo', 'Montevideo (GMT-0300)'), ('America/Montserrat', 'Montserrat (GMT-0400)'), ('America/Nassau', 'Nassau (GMT-0500)'), ('America/New_York', 'New York (GMT-0500)'), ('America/Nipigon', 'Nipigon (GMT-0500)'), ('America/Nome', 'Nome (GMT-0900)'), ('America/Noronha', 'Noronha (GMT-0200)'), ('America/North_Dakota/Beulah', 'Beulah (GMT-0600)'), ('America/North_Dakota/Center', 'Center (GMT-0600)'), ('America/North_Dakota/New_Salem', 'New Salem (GMT-0600)'), ('America/Ojinaga', 'Ojinaga (GMT-0700)'), ('America/Panama', 'Panama (GMT-0500)'), ('America/Pangnirtung', 'Pangnirtung (GMT-0500)'), ('America/Paramaribo', 'Paramaribo (GMT-0300)'), ('America/Phoenix', 'Phoenix (GMT-0700)'), ('America/Port-au-Prince', 'Port-au-Prince (GMT-0500)'), ('America/Port_of_Spain', 'Port of Spain (GMT-0400)'), ('America/Porto_Velho', 'Porto Velho (GMT-0400)'), ('America/Puerto_Rico', 'Puerto Rico (GMT-0400)'), ('America/Rainy_River', 'Rainy River (GMT-0600)'), ('America/Rankin_Inlet', 'Rankin Inlet (GMT-0600)'), ('America/Recife', 'Recife (GMT-0300)'), ('America/Regina', 'Regina (GMT-0600)'), ('America/Resolute', 'Resolute (GMT-0600)'), ('America/Rio_Branco', 'Rio Branco (GMT-0500)'), ('America/Santa_Isabel', 'Santa Isabel (GMT-0800)'), ('America/Santarem', 'Santarem (GMT-0300)'), ('America/Santiago', 'Santiago (GMT-0300)'), ('America/Santo_Domingo', 'Santo Domingo (GMT-0400)'), ('America/Sao_Paulo', 'Sao Paulo (GMT-0200)'), ('America/Scoresbysund', 'Scoresbysund (GMT-0100)'), ('America/Sitka', 'Sitka (GMT-0900)'), ('America/St_Barthelemy', 'St Barthelemy (GMT-0400)'), ('America/St_Johns', 'St Johns (GMT-0330)'), ('America/St_Kitts', 'St Kitts (GMT-0400)'), ('America/St_Lucia', 'St Lucia (GMT-0400)'), ('America/St_Thomas', 'St Thomas (GMT-0400)'), ('America/St_Vincent', 'St Vincent (GMT-0400)'), ('America/Swift_Current', 'Swift Current (GMT-0600)'), ('America/Tegucigalpa', 'Tegucigalpa (GMT-0600)'), ('America/Thule', 'Thule (GMT-0400)'), ('America/Thunder_Bay', 'Thunder Bay (GMT-0500)'), ('America/Tijuana', 'Tijuana (GMT-0800)'), ('America/Toronto', 'Toronto (GMT-0500)'), ('America/Tortola', 'Tortola (GMT-0400)'), ('America/Vancouver', 'Vancouver (GMT-0800)'), ('America/Whitehorse', 'Whitehorse (GMT-0800)'), ('America/Winnipeg', 'Winnipeg (GMT-0600)'), ('America/Yakutat', 'Yakutat (GMT-0900)'), ('America/Yellowknife', 'Yellowknife (GMT-0700)')]), ('Antarctica', [('Antarctica/Casey', 'Casey (GMT+0800)'), ('Antarctica/Davis', 'Davis (GMT+0700)'), ('Antarctica/DumontDUrville', 'DumontDUrville (GMT+1000)'), ('Antarctica/Macquarie', 'Macquarie (GMT+1100)'), ('Antarctica/Mawson', 'Mawson (GMT+0500)'), ('Antarctica/McMurdo', 'McMurdo (GMT+1300)'), ('Antarctica/Palmer', 'Palmer (GMT-0300)'), ('Antarctica/Rothera', 'Rothera (GMT-0300)'), ('Antarctica/Syowa', 'Syowa (GMT+0300)'), ('Antarctica/Troll', 'Troll (GMT+0000)'), ('Antarctica/Vostok', 'Vostok (GMT+0600)')]), ('Arctic', [('Arctic/Longyearbyen', 'Longyearbyen (GMT+0100)')]), ('Asia', [('Asia/Aden', 'Aden (GMT+0300)'), ('Asia/Almaty', 'Almaty (GMT+0600)'), ('Asia/Amman', 'Amman (GMT+0200)'), ('Asia/Anadyr', 'Anadyr (GMT+1200)'), ('Asia/Aqtau', 'Aqtau (GMT+0500)'), ('Asia/Aqtobe', 'Aqtobe (GMT+0500)'), ('Asia/Ashgabat', 'Ashgabat (GMT+0500)'), ('Asia/Baghdad', 'Baghdad (GMT+0300)'), ('Asia/Bahrain', 'Bahrain (GMT+0300)'), ('Asia/Baku', 'Baku (GMT+0400)'), ('Asia/Bangkok', 'Bangkok (GMT+0700)'), ('Asia/Beirut', 'Beirut (GMT+0200)'), ('Asia/Bishkek', 'Bishkek (GMT+0600)'), ('Asia/Brunei', 'Brunei (GMT+0800)'), ('Asia/Chita', 'Chita (GMT+0800)'), ('Asia/Choibalsan', 'Choibalsan (GMT+0800)'), ('Asia/Colombo', 'Colombo (GMT+0530)'), ('Asia/Damascus', 'Damascus (GMT+0200)'), ('Asia/Dhaka', 'Dhaka (GMT+0600)'), ('Asia/Dili', 'Dili (GMT+0900)'), ('Asia/Dubai', 'Dubai (GMT+0400)'), ('Asia/Dushanbe', 'Dushanbe (GMT+0500)'), ('Asia/Gaza', 'Gaza (GMT+0200)'), ('Asia/Hebron', 'Hebron (GMT+0200)'), ('Asia/Ho_Chi_Minh', 'Ho Chi Minh (GMT+0700)'), ('Asia/Hong_Kong', 'Hong Kong (GMT+0800)'), ('Asia/Hovd', 'Hovd (GMT+0700)'), ('Asia/Irkutsk', 'Irkutsk (GMT+0800)'), ('Asia/Jakarta', 'Jakarta (GMT+0700)'), ('Asia/Jayapura', 'Jayapura (GMT+0900)'), ('Asia/Jerusalem', 'Jerusalem (GMT+0200)'), ('Asia/Kabul', 'Kabul (GMT+0430)'), ('Asia/Kamchatka', 'Kamchatka (GMT+1200)'), ('Asia/Karachi', 'Karachi (GMT+0500)'), ('Asia/Kathmandu', 'Kathmandu (GMT+0545)'), ('Asia/Khandyga', 'Khandyga (GMT+0900)'), ('Asia/Kolkata', 'Kolkata (GMT+0530)'), ('Asia/Krasnoyarsk', 'Krasnoyarsk (GMT+0700)'), ('Asia/Kuala_Lumpur', 'Kuala Lumpur (GMT+0800)'), ('Asia/Kuching', 'Kuching (GMT+0800)'), ('Asia/Kuwait', 'Kuwait (GMT+0300)'), ('Asia/Macau', 'Macau (GMT+0800)'), ('Asia/Magadan', 'Magadan (GMT+1000)'), ('Asia/Makassar', 'Makassar (GMT+0800)'), ('Asia/Manila', 'Manila (GMT+0800)'), ('Asia/Muscat', 'Muscat (GMT+0400)'), ('Asia/Nicosia', 'Nicosia (GMT+0200)'), ('Asia/Novokuznetsk', 'Novokuznetsk (GMT+0700)'), ('Asia/Novosibirsk', 'Novosibirsk (GMT+0600)'), ('Asia/Omsk', 'Omsk (GMT+0600)'), ('Asia/Oral', 'Oral (GMT+0500)'), ('Asia/Phnom_Penh', 'Phnom Penh (GMT+0700)'), ('Asia/Pontianak', 'Pontianak (GMT+0700)'), ('Asia/Pyongyang', 'Pyongyang (GMT+0830)'), ('Asia/Qatar', 'Qatar (GMT+0300)'), ('Asia/Qyzylorda', 'Qyzylorda (GMT+0600)'), ('Asia/Rangoon', 'Rangoon (GMT+0630)'), ('Asia/Riyadh', 'Riyadh (GMT+0300)'), ('Asia/Sakhalin', 'Sakhalin (GMT+1000)'), ('Asia/Samarkand', 'Samarkand (GMT+0500)'), ('Asia/Seoul', 'Seoul (GMT+0900)'), ('Asia/Shanghai', 'Shanghai (GMT+0800)'), ('Asia/Singapore', 'Singapore (GMT+0800)'), ('Asia/Srednekolymsk', 'Srednekolymsk (GMT+1100)'), ('Asia/Taipei', 'Taipei (GMT+0800)'), ('Asia/Tashkent', 'Tashkent (GMT+0500)'), ('Asia/Tbilisi', 'Tbilisi (GMT+0400)'), ('Asia/Tehran', 'Tehran (GMT+0330)'), ('Asia/Thimphu', 'Thimphu (GMT+0600)'), ('Asia/Tokyo', 'Tokyo (GMT+0900)'), ('Asia/Ulaanbaatar', 'Ulaanbaatar (GMT+0800)'), ('Asia/Urumqi', 'Urumqi (GMT+0600)'), ('Asia/Ust-Nera', 'Ust-Nera (GMT+1000)'), ('Asia/Vientiane', 'Vientiane (GMT+0700)'), ('Asia/Vladivostok', 'Vladivostok (GMT+1000)'), ('Asia/Yakutsk', 'Yakutsk (GMT+0900)'), ('Asia/Yekaterinburg', 'Yekaterinburg (GMT+0500)'), ('Asia/Yerevan', 'Yerevan (GMT+0400)')]), ('Atlantic', [('Atlantic/Azores', 'Azores (GMT-0100)'), ('Atlantic/Bermuda', 'Bermuda (GMT-0400)'), ('Atlantic/Canary', 'Canary (GMT+0000)'), ('Atlantic/Cape_Verde', 'Cape Verde (GMT-0100)'), ('Atlantic/Faroe', 'Faroe (GMT+0000)'), ('Atlantic/Madeira', 'Madeira (GMT+0000)'), ('Atlantic/Reykjavik', 'Reykjavik (GMT+0000)'), ('Atlantic/South_Georgia', 'South Georgia (GMT-0200)'), ('Atlantic/St_Helena', 'St Helena (GMT+0000)'), ('Atlantic/Stanley', 'Stanley (GMT-0300)')]), ('Australia', [('Australia/Adelaide', 'Adelaide (GMT+1030)'), ('Australia/Brisbane', 'Brisbane (GMT+1000)'), ('Australia/Broken_Hill', 'Broken Hill (GMT+1030)'), ('Australia/Currie', 'Currie (GMT+1100)'), ('Australia/Darwin', 'Darwin (GMT+0930)'), ('Australia/Eucla', 'Eucla (GMT+0845)'), ('Australia/Hobart', 'Hobart (GMT+1100)'), ('Australia/Lindeman', 'Lindeman (GMT+1000)'), ('Australia/Lord_Howe', 'Lord Howe (GMT+1100)'), ('Australia/Melbourne', 'Melbourne (GMT+1100)'), ('Australia/Perth', 'Perth (GMT+0800)'), ('Australia/Sydney', 'Sydney (GMT+1100)')]), ('Canada', [('Canada/Atlantic', 'Atlantic (GMT-0400)'), ('Canada/Central', 'Central (GMT-0600)'), ('Canada/Eastern', 'Eastern (GMT-0500)'), ('Canada/Mountain', 'Mountain (GMT-0700)'), ('Canada/Newfoundland', 'Newfoundland (GMT-0330)'), ('Canada/Pacific', 'Pacific (GMT-0800)')]), ('Europe', [('Europe/Amsterdam', 'Amsterdam (GMT+0100)'), ('Europe/Andorra', 'Andorra (GMT+0100)'), ('Europe/Athens', 'Athens (GMT+0200)'), ('Europe/Belgrade', 'Belgrade (GMT+0100)'), ('Europe/Berlin', 'Berlin (GMT+0100)'), ('Europe/Bratislava', 'Bratislava (GMT+0100)'), ('Europe/Brussels', 'Brussels (GMT+0100)'), ('Europe/Bucharest', 'Bucharest (GMT+0200)'), ('Europe/Budapest', 'Budapest (GMT+0100)'), ('Europe/Busingen', 'Busingen (GMT+0100)'), ('Europe/Chisinau', 'Chisinau (GMT+0200)'), ('Europe/Copenhagen', 'Copenhagen (GMT+0100)'), ('Europe/Dublin', 'Dublin (GMT+0000)'), ('Europe/Gibraltar', 'Gibraltar (GMT+0100)'), ('Europe/Guernsey', 'Guernsey (GMT+0000)'), ('Europe/Helsinki', 'Helsinki (GMT+0200)'), ('Europe/Isle_of_Man', 'Isle of Man (GMT+0000)'), ('Europe/Istanbul', 'Istanbul (GMT+0200)'), ('Europe/Jersey', 'Jersey (GMT+0000)'), ('Europe/Kaliningrad', 'Kaliningrad (GMT+0200)'), ('Europe/Kiev', 'Kiev (GMT+0200)'), ('Europe/Lisbon', 'Lisbon (GMT+0000)'), ('Europe/Ljubljana', 'Ljubljana (GMT+0100)'), ('Europe/London', 'London (GMT+0000)'), ('Europe/Luxembourg', 'Luxembourg (GMT+0100)'), ('Europe/Madrid', 'Madrid (GMT+0100)'), ('Europe/Malta', 'Malta (GMT+0100)'), ('Europe/Mariehamn', 'Mariehamn (GMT+0200)'), ('Europe/Minsk', 'Minsk (GMT+0300)'), ('Europe/Monaco', 'Monaco (GMT+0100)'), ('Europe/Moscow', 'Moscow (GMT+0300)'), ('Europe/Oslo', 'Oslo (GMT+0100)'), ('Europe/Paris', 'Paris (GMT+0100)'), ('Europe/Podgorica', 'Podgorica (GMT+0100)'), ('Europe/Prague', 'Prague (GMT+0100)'), ('Europe/Riga', 'Riga (GMT+0200)'), ('Europe/Rome', 'Rome (GMT+0100)'), ('Europe/Samara', 'Samara (GMT+0400)'), ('Europe/San_Marino', 'San Marino (GMT+0100)'), ('Europe/Sarajevo', 'Sarajevo (GMT+0100)'), ('Europe/Simferopol', 'Simferopol (GMT+0300)'), ('Europe/Skopje', 'Skopje (GMT+0100)'), ('Europe/Sofia', 'Sofia (GMT+0200)'), ('Europe/Stockholm', 'Stockholm (GMT+0100)'), ('Europe/Tallinn', 'Tallinn (GMT+0200)'), ('Europe/Tirane', 'Tirane (GMT+0100)'), ('Europe/Uzhgorod', 'Uzhgorod (GMT+0200)'), ('Europe/Vaduz', 'Vaduz (GMT+0100)'), ('Europe/Vatican', 'Vatican (GMT+0100)'), ('Europe/Vienna', 'Vienna (GMT+0100)'), ('Europe/Vilnius', 'Vilnius (GMT+0200)'), ('Europe/Volgograd', 'Volgograd (GMT+0300)'), ('Europe/Warsaw', 'Warsaw (GMT+0100)'), ('Europe/Zagreb', 'Zagreb (GMT+0100)'), ('Europe/Zaporozhye', 'Zaporozhye (GMT+0200)'), ('Europe/Zurich', 'Zurich (GMT+0100)')]), ('GMT', [('GMT', 'GMT (GMT+0000)')]), ('Indian', [('Indian/Antananarivo', 'Antananarivo (GMT+0300)'), ('Indian/Chagos', 'Chagos (GMT+0600)'), ('Indian/Christmas', 'Christmas (GMT+0700)'), ('Indian/Cocos', 'Cocos (GMT+0630)'), ('Indian/Comoro', 'Comoro (GMT+0300)'), ('Indian/Kerguelen', 'Kerguelen (GMT+0500)'), ('Indian/Mahe', 'Mahe (GMT+0400)'), ('Indian/Maldives', 'Maldives (GMT+0500)'), ('Indian/Mauritius', 'Mauritius (GMT+0400)'), ('Indian/Mayotte', 'Mayotte (GMT+0300)'), ('Indian/Reunion', 'Reunion (GMT+0400)')]), ('Pacific', [('Pacific/Apia', 'Apia (GMT+1400)'), ('Pacific/Auckland', 'Auckland (GMT+1300)'), ('Pacific/Bougainville', 'Bougainville (GMT+1100)'), ('Pacific/Chatham', 'Chatham (GMT+1345)'), ('Pacific/Chuuk', 'Chuuk (GMT+1000)'), ('Pacific/Easter', 'Easter (GMT-0500)'), ('Pacific/Efate', 'Efate (GMT+1100)'), ('Pacific/Enderbury', 'Enderbury (GMT+1300)'), ('Pacific/Fakaofo', 'Fakaofo (GMT+1300)'), ('Pacific/Fiji', 'Fiji (GMT+1200)'), ('Pacific/Funafuti', 'Funafuti (GMT+1200)'), ('Pacific/Galapagos', 'Galapagos (GMT-0600)'), ('Pacific/Gambier', 'Gambier (GMT-0900)'), ('Pacific/Guadalcanal', 'Guadalcanal (GMT+1100)'), ('Pacific/Guam', 'Guam (GMT+1000)'), ('Pacific/Honolulu', 'Honolulu (GMT-1000)'), ('Pacific/Johnston', 'Johnston (GMT-1000)'), ('Pacific/Kiritimati', 'Kiritimati (GMT+1400)'), ('Pacific/Kosrae', 'Kosrae (GMT+1100)'), ('Pacific/Kwajalein', 'Kwajalein (GMT+1200)'), ('Pacific/Majuro', 'Majuro (GMT+1200)'), ('Pacific/Marquesas', 'Marquesas (GMT-0930)'), ('Pacific/Midway', 'Midway (GMT-1100)'), ('Pacific/Nauru', 'Nauru (GMT+1200)'), ('Pacific/Niue', 'Niue (GMT-1100)'), ('Pacific/Norfolk', 'Norfolk (GMT+1100)'), ('Pacific/Noumea', 'Noumea (GMT+1100)'), ('Pacific/Pago_Pago', 'Pago Pago (GMT-1100)'), ('Pacific/Palau', 'Palau (GMT+0900)'), ('Pacific/Pitcairn', 'Pitcairn (GMT-0800)'), ('Pacific/Pohnpei', 'Pohnpei (GMT+1100)'), ('Pacific/Port_Moresby', 'Port Moresby (GMT+1000)'), ('Pacific/Rarotonga', 'Rarotonga (GMT-1000)'), ('Pacific/Saipan', 'Saipan (GMT+1000)'), ('Pacific/Tahiti', 'Tahiti (GMT-1000)'), ('Pacific/Tarawa', 'Tarawa (GMT+1200)'), ('Pacific/Tongatapu', 'Tongatapu (GMT+1300)'), ('Pacific/Wake', 'Wake (GMT+1200)'), ('Pacific/Wallis', 'Wallis (GMT+1200)')]), ('US', [('US/Alaska', 'Alaska (GMT-0900)'), ('US/Arizona', 'Arizona (GMT-0700)'), ('US/Central', 'Central (GMT-0600)'), ('US/Eastern', 'Eastern (GMT-0500)'), ('US/Hawaii', 'Hawaii (GMT-1000)'), ('US/Mountain', 'Mountain (GMT-0700)'), ('US/Pacific', 'Pacific (GMT-0800)')]), ('UTC', [('UTC', 'UTC (GMT+0000)')])])),
                ('locale', models.CharField(default=b'en-US', choices=[(b'af', 'Afrikaans'), (b'ar', '\u0639\u0631\u0628\u064a'), (b'az', 'Az\u0259rbaycanca'), (b'bm', 'Bamanankan'), (b'bn-BD', '\u09ac\u09be\u0982\u09b2\u09be (\u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6)'), (b'bn-IN', '\u09ac\u09be\u0982\u09b2\u09be (\u09ad\u09be\u09b0\u09a4)'), (b'ca', 'Catal\xe0'), (b'cs', '\u010ce\u0161tina'), (b'de', 'Deutsch'), (b'ee', 'E\u028be'), (b'el', '\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac'), (b'en-US', 'English (US)'), (b'es', 'Espa\xf1ol'), (b'fa', '\u0641\u0627\u0631\u0633\u06cc'), (b'ff', 'Pulaar-Fulfulde'), (b'fi', 'suomi'), (b'fr', 'Fran\xe7ais'), (b'fy-NL', 'Frysk'), (b'ga-IE', 'Gaeilge'), (b'ha', 'Hausa'), (b'he', '\u05e2\u05d1\u05e8\u05d9\u05ea'), (b'hi-IN', '\u0939\u093f\u0928\u094d\u0926\u0940 (\u092d\u093e\u0930\u0924)'), (b'hr', 'Hrvatski'), (b'hu', 'magyar'), (b'id', 'Bahasa Indonesia'), (b'ig', 'Igbo'), (b'it', 'Italiano'), (b'ja', '\u65e5\u672c\u8a9e'), (b'ka', '\u10e5\u10d0\u10e0\u10d7\u10e3\u10da\u10d8'), (b'ko', '\ud55c\uad6d\uc5b4'), (b'ln', 'Ling\xe1la'), (b'mg', 'Malagasy'), (b'ml', '\u0d2e\u0d32\u0d2f\u0d3e\u0d33\u0d02'), (b'ms', 'Melayu'), (b'my', '\u1019\u103c\u1014\u103a\u1019\u102c\u1018\u102c\u101e\u102c'), (b'nl', 'Nederlands'), (b'pl', 'Polski'), (b'pt-BR', 'Portugu\xeas (do\xa0Brasil)'), (b'pt-PT', 'Portugu\xeas (Europeu)'), (b'ro', 'Rom\xe2n\u0103'), (b'ru', '\u0420\u0443\u0441\u0441\u043a\u0438\u0439'), (b'son', 'So\u014bay'), (b'sq', 'Shqip'), (b'sr', '\u0421\u0440\u043f\u0441\u043a\u0438'), (b'sr-Latn', 'Srpski'), (b'sv-SE', 'Svenska'), (b'sw', 'Kiswahili'), (b'ta', '\u0ba4\u0bae\u0bbf\u0bb4\u0bcd'), (b'th', '\u0e44\u0e17\u0e22'), (b'tl', 'Tagalog'), (b'tn', 'Setswana'), (b'tr', 'T\xfcrk\xe7e'), (b'uk', '\u0423\u043a\u0440\u0430\u0457\u043d\u0441\u044c\u043a\u0430'), (b'vi', 'Ti\u1ebfng Vi\u1ec7t'), (b'wo', 'Wolof'), (b'xh', 'isiXhosa'), (b'yo', 'Yor\xf9b\xe1'), (b'zh-CN', '\u4e2d\u6587 (\u7b80\u4f53)'), (b'zh-TW', '\u6b63\u9ad4\u4e2d\u6587 (\u7e41\u9ad4)'), (b'zu', 'isiZulu')], max_length=7, blank=True, verbose_name='Language', db_index=True)),
                ('homepage', models.URLField(blank=True, max_length=255, verbose_name='Homepage', error_messages={b'invalid': 'This URL has an invalid format. Valid URLs look like http://example.com/my_page.'})),
                ('title', models.CharField(max_length=255, verbose_name='Title', blank=True)),
                ('fullname', models.CharField(max_length=255, verbose_name='Name', blank=True)),
                ('organization', models.CharField(max_length=255, verbose_name='Organization', blank=True)),
                ('location', models.CharField(max_length=255, verbose_name='Location', blank=True)),
                ('bio', models.TextField(verbose_name='About Me', blank=True)),
                ('irc_nickname', models.CharField(max_length=255, verbose_name='IRC nickname', blank=True)),
                ('website_url', models.TextField(blank=True, verbose_name='Website', validators=[django.core.validators.RegexValidator(b'^https?://', 'Enter a valid website URL.', b'invalid')])),
                ('mozillians_url', models.TextField(blank=True, verbose_name='Mozillians', validators=[django.core.validators.RegexValidator(b'^https?://mozillians\\.org/u/', 'Enter a valid Mozillians URL.', b'invalid')])),
                ('github_url', models.TextField(blank=True, verbose_name='GitHub', validators=[django.core.validators.RegexValidator(b'^https?://github\\.com/', 'Enter a valid GitHub URL.', b'invalid')])),
                ('twitter_url', models.TextField(blank=True, verbose_name='Twitter', validators=[django.core.validators.RegexValidator(b'^https?://twitter\\.com/', 'Enter a valid Twitter URL.', b'invalid')])),
                ('linkedin_url', models.TextField(blank=True, verbose_name='LinkedIn', validators=[django.core.validators.RegexValidator(b'^https?://((www|\\w\\w)\\.)?linkedin.com/((in/[^/]+/?)|(pub/[^/]+/((\\w|\\d)+/?){3}))$', 'Enter a valid LinkedIn URL.', b'invalid')])),
                ('facebook_url', models.TextField(blank=True, verbose_name='Facebook', validators=[django.core.validators.RegexValidator(b'^https?://www\\.facebook\\.com/', 'Enter a valid Facebook URL.', b'invalid')])),
                ('stackoverflow_url', models.TextField(blank=True, verbose_name='Stack Overflow', validators=[django.core.validators.RegexValidator(b'^https?://stackoverflow\\.com/users/', 'Enter a valid Stack Overflow URL.', b'invalid')])),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
                ('tags', kuma.core.managers.NamespacedTaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'db_table': 'auth_user',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='UserBan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reason', models.TextField()),
                ('date', models.DateField(default=datetime.date.today)),
                ('is_active', models.BooleanField(default=True, help_text=b'(Is ban active)')),
                ('by', models.ForeignKey(related_name='bans_issued', verbose_name=b'Banned by', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='bans', verbose_name=b'Banned user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
