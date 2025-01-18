das Plugin ist eine Adaption des AutoShutDown für Python2 und Python3
der neue Name deshalb, weil mir vom damaligen Dev des VTi angeraten wurde dies zu tun, um Überschreiben und Verwechslungen auszuschließen
ich habe das Original etwas abgeändert und um einiges erweitert, jedoch in der Bedienung versucht so nahe wie möglich am gewohnten zu bleiben


wichtigste Änderungen:

- zum Abbrechen genügt eine beliebige Taste (außer Steuerkreuz runter+OK)
(wenn ich eingreife, dann sicher nicht um zu bestätigen das ich nicht abbrechen will, also so wenig wie möglich Tasten...)

- das 'brutale' abschalten kann mittels langsam absenkender Lautstärke abgemildert werden
(um nicht gerade dadurch wieder geweckt zu werden)
wie schnell die Lautstärke abgesenkt wird ist einstellbar, sollte man mal ausprobieren was einem angenehm erscheint


- einstellbar ist, dass bei Inaktivität bis zum Ende der Sendung gewartet wird. 
Es ist unschön, wenn die Zeitabschaltung immer mitten in irgendwelchen Sendungen greift
(funktioniert nur so zuverlässig, wie die now-/next-Funktion im System bzw. Erkennung der Dateilänge)

    Einstellungen dafür:
    * nächste Sendung wenn weniger -> wenn die aktuelle Sendung weniger als diese Angabe dauert, wird das Ende der folgenden Sendung gewählt
    (wenn beim Einschalten die Sendung in 4min zu Ende ist, will sicher niemand ausschalten lassen..)
    * reagieren spätestens -> falls keine Ende-Zeit erkannt wird oder diese länger ist als hier eingestellt, wird stur nach diesen Minuten getimert
