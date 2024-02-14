das Plugin ist eine Adaption des AutoShutDown für Python2 und Python3
der neue Name deshalb, weil mir vom damaligen Dev des VTi angeraten wurde dies zu tun, um Überschreiben und Verwechslungen auszuschließen
ich habe das Original etwas abgeändert und um einiges erweitert, jedoch in der Bedienung versucht so nahe wie möglich am gewohnten zu bleiben


wichtigste Änderungen:

- zum Abbrechen genügt eine beliebige Taste (außer Steuerkreuz runter+OK)
(wenn ich eingreife, dann sicher nicht um zu bestätigen das ich nicht abbrechen will, also so wenig wie möglich Tasten...)


- einstellbar ist, dass zusätzlich zur Dauer der Inaktivität anschließend bis zum Ende der Sendung gewartet wird
es ist unschön, wenn die Zeitabschaltung immer mitten in irgendwelchen Sendungen greift
funktioniert nur so zuverlässig, wie die now-/next-Funktion im System bzw. Erkennung der Dateilänge
(Beispiel: wenn bei Inaktivität 15min eingestellt sind, dann wird nach einer Sendung länger als 15min abgeschaltet, wenn jedoch das Ende in 10min ist dann wird zur Abschaltung das Ende der nächsten Sendung verwendet)


- das 'brutale' abschalten kann mittels langsam absenkender Lautstärke abgemildert werden
(um nicht gerade dadurch wieder geweckt zu werden)
wie schnell die Lautstärke abgesenkt wird ist einstellbar, sollte man mal ausprobieren was einem angenehm erscheint 
