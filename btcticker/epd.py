def get_epd(epd_type):
    epd = None
    mirror = False
    width_first = True
    Use4Gray = False
    Init4Gray = False
    FullUpdate = False

    if epd_type == "1in02":
        from waveshare_epd import epd1in02

        epd = epd1in02.EPD()
    elif epd_type == "1in54":
        from waveshare_epd import epd1in54

        epd = epd1in54.EPD()
    elif epd_type == "1in54_V2":
        from waveshare_epd import epd1in54

        epd = epd1in54_V2.EPD()
    elif epd_type == "1in54b":
        from waveshare_epd import epd1in54b

        epd = epd1in54b.EPD()
    elif epd_type == "1in54b_V2":
        from waveshare_epd import epd1in54b_V2

        epd = epd1in54b_V2.EPD()
    elif epd_type == "1in54c":
        from waveshare_epd import epd1in54c

        epd = epd1in54c.EPD()
    elif epd_type == "1in64g":
        from waveshare_epd import epd1in64g

        epd = epd1in64g.EPD()
    elif epd_type == "2in13":
        from waveshare_epd import epd2in13

        epd = epd2in13.EPD()
    elif epd_type == "2in13_V2":
        from waveshare_epd import epd2in13_V2

        epd = epd2in13_V2.EPD()
    elif epd_type == "2in13_V3":
        from waveshare_epd import epd2in13_V3

        epd = epd2in13_V3.EPD()
    elif epd_type == "2in13b_V3":
        from waveshare_epd import epd2in13b_V3

        epd = epd2in13b_V3.EPD()
    elif epd_type == "2in13b_V4":
        from waveshare_epd import epd2in13b_V4

        epd = epd2in13b_V4.EPD()
    elif epd_type == "2in13bc":
        from waveshare_epd import epd2in13bc

        epd = epd2in13bc.EPD()
    elif epd_type == "2in13d":
        from waveshare_epd import epd2in13d

        epd = epd2in13d.EPD()
    elif epd_type == "2in36g":
        from waveshare_epd import epd2in36g

        epd = epd2in36g.EPD()
    elif epd_type == "2in66":
        from waveshare_epd import epd2in66

        epd = epd2in66.EPD()
    elif epd_type == "2in66b":
        from waveshare_epd import epd2in66b

        epd = epd2in66b.EPD()
    elif epd_type == "2in7":
        from waveshare_epd import epd2in7

        epd = epd2in7.EPD()
    elif epd_type == "2in7_V2":
        from waveshare_epd import epd2in7_V2

        epd = epd2in7_V2.EPD()
    elif epd_type == "2in7b":
        from waveshare_epd import epd2in7b

        epd = epd2in7b.EPD()
    elif epd_type == "2in7b_V2":
        from waveshare_epd import epd2in7b_V2

        epd = epd2in7b_V2.EPD()
    elif epd_type == "2in9":
        from waveshare_epd import epd2in9

        epd = epd2in9.EPD()
    elif epd_type == "2in9_V2":
        from waveshare_epd import epd2in9_V2

        epd = epd2in9_V2.EPD()
    elif epd_type == "2in9b_V3":
        from waveshare_epd import epd2in9b_V3

        epd = epd2in9b_V3.EPD()
    elif epd_type == "2in9bc":
        from waveshare_epd import epd2in9bc

        epd = epd2in9bc.EPD()
    elif epd_type == "2in9d":
        from waveshare_epd import epd2in9d

        epd = epd2in9d.EPD()
    elif epd_type == "3in0g":
        from waveshare_epd import epd3in0g

        epd = epd3in0g.EPD()
    elif epd_type == "3in52":
        from waveshare_epd import epd3in52

        epd = epd3in52.EPD()
    elif epd_type == "3in7":
        from waveshare_epd import epd3in7

        Use4Gray = True
        epd = epd3in7.EPD()
    elif epd_type == "4in01f":
        from waveshare_epd import epd4in01f

        epd = epd4in01f.EPD()
    elif epd_type == "4in2":
        from waveshare_epd import epd4in2

        epd = epd4in2.EPD()
    elif epd_type == "4in2b_V2":
        from waveshare_epd import epd4in2b_V2

        epd = epd4in2b_V2.EPD()
    elif epd_type == "4in2bc":
        from waveshare_epd import epd4in2bc

        epd = epd4in2bc.EPD()
    elif epd_type == "4in37g":
        from waveshare_epd import epd4in37g

        epd = epd4in37g.EPD()
    elif epd_type == "5in65f":
        from waveshare_epd import epd5in65f

        epd = epd5in65f.EPD()
    elif epd_type == "5in83":
        from waveshare_epd import epd5in83

        epd = epd5in83.EPD()
    elif epd_type == "5in83_V2":
        from waveshare_epd import epd5in83_V2

        epd = epd5in83_V2.EPD()
    elif epd_type == "5in83b_V2":
        from waveshare_epd import epd5in83b_V2

        epd = epd5in83b_V2.EPD()
    elif epd_type == "5in83bc":
        from waveshare_epd import epd5in83bc

        epd = epd5in83bc.EPD()
    elif epd_type == "7in3f":
        from waveshare_epd import epd7in3f

        epd = epd7in3f.EPD()
    elif epd_type == "7in3g":
        from waveshare_epd import epd7in3g

        epd = epd7in3g.EPD()
    elif epd_type == "7in5":
        from waveshare_epd import epd7in5

        epd = epd7in5.EPD()
        width_first = False
    elif epd_type == "7in5_HD":
        from waveshare_epd import epd7in5_HD

        epd = epd7in5_HD.EPD()
        width_first = False
    elif epd_type == "7in5_V2":
        from waveshare_epd import epd7in5_V2

        width_first = False
        epd = epd7in5_V2.EPD()
    elif epd_type == "7in5b_HD":
        from waveshare_epd import epd7in5b_HD

        width_first = False
        epd = epd7in5b_HD.EPD()
    elif epd_type == "7in5b_V2":
        from waveshare_epd import epd7in5b_V2

        epd = epd7in5b_V2.EPD()
        width_first = False
    elif epd_type == "7in5bc":
        from waveshare_epd import epd7in5bc

        epd = epd7in5bc.EPD()
        width_first = False
    elif epd_type == "TP_epd2in13_V2":
        from TP_lib import epd2in13_V2 as TP_epd2in13_V2

        epd = TP_epd2in13_V2.EPD()
        FullUpdate = True
    elif epd_type == "TP_epd2in13_V3":
        from TP_lib import epd2in13_V3 as TP_epd2in13_V3

        epd = TP_epd2in13_V3.EPD()
        FullUpdate = True
    elif epd_type == "TP_epd2in13_V4":
        from TP_lib import epd2in13_V4 as TP_epd2in13_V4

        epd = TP_epd2in13_V4.EPD()
        FullUpdate = True
    elif epd_type == "TP_epd2in9_V2":
        from TP_lib import epd2in9_V2 as TP_epd2in9_V2

        epd = TP_epd2in9_V2.EPD()
        FullUpdate = True
    elif epd_type == "2in7_4gray":
        from waveshare_epd import epd2in7

        epd = epd2in7.EPD()
        Use4Gray = True
        Init4Gray = True
    elif epd_type == "3in7_4gray":
        from waveshare_epd import epd3in7

        epd = epd3in7.EPD()
        Use4Gray = True
        Init4Gray = True
    else:
        raise Exception("Wrong epd_type")
    return epd, mirror, width_first, Use4Gray, Init4Gray, FullUpdate
