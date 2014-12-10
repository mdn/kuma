#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from identify import LanguageIdentifier


TEXT = """
Ästhetik des "Erhabenen" herangezogen.
kostete (hinzu kommen über 6 630 tote
   O3 steht für Ozon; es wird in der
NO2 sind wesentlich am "sauren Regen"
Ethik hängt eng mit einer Dauerkrise der
Serumwerk GmbH Dresden, Postfach
,Hundeschläger' für die Dezimierung der
Momente ihrer Erfahrung".
zusammen.
ihren Kampf um Boden wie um
Unsinn, weil die Leute Unsinn wollen
Ressourcen als soziales Entwicklungsproblem".
der Leunabrücke durch Kommune,
Speiseröhre oder bei Atemstörungen von
hob er hervor, daß die Knorpel
"Reisekader" wurden zu DDR-Zeiten
für die soziale Verständigung zugesprochen
hinaus noch viele Fähigkeiten entwickelte.
Adorno).
Frankfurter Vereine. Und
die erste evangelische Schule hatte
beispielsweise die Pfarrkirche, das
gebracht. Offenbar spielt die Schlafposition
Menschlichkeit oder Rechtsstaatlichkeit
Die nun geplante Straße würde im
zum Thema "Der psychisch kranke
ergaben im Zeitraum von 1986 bis 1989
junge Leute sind oft zahlungskräftig in
unter die Bettdecke gerate, könne es sich
Schäden hinterläßt, berechtigt
körperlichen Belastbarkeit. Tatsächlich
von der Drogenpolitik zu reden) oder
Parlament unter syrischem Druck diesen
Jahrhunderten der wuchtige Turm für
auf die Frage aus, wie sich Eltern verhalten
ehemalige Generalsekretär der Partei,
Mark erhöht", sagt Hühsam, "das war bei
Über eine Annonce in einem Frankfurter
der Töpfer ein. Anhand von gefundenen
gut kennt, hatte ihm die wahren Tatsachen
Sechzehn Adorno-Schüler erinnern
und daß ein Weiterdenken der Theorie
für ihre Festlegung sind drei Jahre
Erschütterung Einblick in die Abhängigkeit
der Bauarbeiten sei erst im Laufe des
als neuen Kometen am Kandidatenhimmel
ergaben im Zeitraum von 1986 bis 1989
- ein neuer Beitrag zur Fortschreibung
Triptychon im Sitzungssaal des Ortsbeirates
Karin gab später ein bemerkenswertes
mit dem er darüber reden konnte?
Kunstwerk niemals das Ganze (der Welt
junge Talente vor, die vielleicht irgendwo
der AG Schweizer Straße, einer Initiative
für Stickstoffdioxid; diese Substanzen
Tätigkeit in erster Linie das sportliche
kommentiert worden, sowohl skeptisch
auch durch "eine Unmenge Zuschriften
Grundschule, in deren Gebäude auch die
gegen Streß und die sexuelle Attraktivität.
Pablo Tattay und Henry Caballero aus
besteht für die Leunabrücke keine rechtliche
auf einem Parteikongreß mittels Abstimmung
Laurentiuskirche.
später der SED beitraten?" Es ist der
- und die Leute wollen Unsinn, weil
früh geboren wurden oder an Muskelschwäche
Grundlage. "Bei einem Brückenbau
Mensch" auf, als ein automatisch flirtender.
und sich inzwischen als Operateur
xx  = Schadstoff wird dort nicht
sondern auch für die Geschäftsleute.
Kommunismus eintreten würde. In ihren
NCV-Vorsitzender Rainer Schroth ehrte
Aufsicht bereit sind. *leo
Daseins, in dem sie Möglichkeiten einer
die alten Schwanheimer?" in der
können sich ein Lachen nicht verkneifen.
ist". Die "gesunde Mischung" aus edlen
genannt hatte: "Junger Freund,
ist vorbeugend schon 1936 von Adorno
Ruhe ein", sagt Jens. Ruhe vor den
Ökologie bald auch
englischen Rasen der Nachbarn. Schon
Forschungsarbeit sich doch noch hat habilitieren
dringend davor, Säuglinge in den ersten
Milligramm je Kubikmeter
Im Gespräch: Indianer aus Kolumbien
wenige Fälle von Plötzlichem Kindstod.
   Für nicht empfehlenswert hält er Fußball
   SO2 steht für Schwefeldioxid, NO2
Schwanheimer Unterfeldes hin. Rund 110
Adorno 1957 auf eine törichte Dissonanz-Rezension
durch Laute, Lächeln und Greifen
und kamen, um abzustimmen." Doch
daß genau das nach dem Ende des
Zedillo, erst vor kurzem ins Erziehungsministerium
"andere Geschichte", die "unlogische".
Übungen zu integrieren und somit wenigstens
Ausmaße angenommen. Überall wimmelte
ambulant - einen Namen gemacht hat.
Kiesgruben im Unterfeld als
der in der Verfassung festgeschriebenen
Seit 1975 habe er in seinem Fachgebiet
Feuilletons eingerissene Methode, durch
ganz woanders, schon damals
mehr zu machen." Heute verkauft dort
für das existentielle Bewußtsein belegen.
überhöht und verklärt als durchdringt
  Tatsächlich hat sich die durchschnittliche
"sehr, sehr schwer". Alle aber entwikkelten
der Bauchlage aufgeklärt wurde, ging der
- und die Leute wollen Unsinn, weil
in der einen Hand das Frühstücksbrötchen,
besitzen. Solche Sportarten
mit einer Aktion zusammen,
nach Bornheim wanderten, um ihren
sind, an den Ausführungsbestimmungen.
Um eventuelle Entsorgungskosten zu
junge Leute sind oft zahlungskräftig in
Zwar versicherte der syrische Vizepräsident
einem internen Korrektiv der Ethik.
Eckpfeiler der einstigen Stadtbefestigung
durchstieß er, als er den Arm auf die
hat es ihm nachgemacht. Und auch
nachgedacht, wie sein Leben wohl verlaufen
wie hoffnungsvoll: "Wie die Toten wehrlos
und ging besonders auf das Handwerk
Syrien.
KLAUS DALLIBOR
Brüche glättete, steht er zukünftig
und erschüttert, wird Ästhetik zu
Fitneß-Studio individuell abgestimmte
der Strenge des Bilderverbots.
Carneval-Vereins (NCV) beim traditionellen
bringen, ohne sie dem Diktat versöhnender
und in den Karnevalvereinen -
"""


class TestLanguageIdentifier(object):
    def setup_class(self):
        self.langident = LanguageIdentifier()

    def test_identify_lang(self):
        assert self.langident.identify_lang('') == None
        assert self.langident.identify_lang(TEXT) == 'de'
