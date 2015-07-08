#!/usr/bin/env python
#
# A very simple example that creates a random image from the
# PseudoGimpy CAPTCHA, saves and shows it, and prints the list
# of solutions. Normally you would call testSolutions rather
# than reading this list yourself.
#
#from Captcha.Visual.Tests import PseudoGimpy, AngryGimpy, AntiSpam
#g = PseudoGimpy()
#g = AngryGimpy()
#g = AntiSpam()

from Captcha.Visual import Text, Backgrounds, Distortions, ImageCaptcha
from Captcha import Words
import random

class CustomTest(ImageCaptcha):
    def __init__(self, *args, **kwargs):
        self.word = kwargs['word']
        del kwargs['word']
        super(CustomTest, self).__init__(*args, **kwargs)

    def getLayers(self):
        #word = Words.defaultWordList.pick()
        self.addSolution(self.word)
        #return [
            #Backgrounds.SolidColor(),
            #random.choice([
                #Backgrounds.CroppedImage(),
                #Backgrounds.TiledImage(),
            #    Backgrounds.Grid(size=10)
            #]),
            #Text.TextLayer(word, borderSize=1),
            #Backgrounds.Grid(size=15),
            #Distortions.SineWarp(amplitudeRange=(2, 3.0)),
            #Distortions.WigglyBlocks(blockSize=5),
            #Backgrounds.RandomDots(dotSize=2, numDots=400),
        #    ]

        return [
            Backgrounds.SolidColor(),
            Backgrounds.Grid(size=10),
            Distortions.SineWarp(amplitudeRange=(3, 5.0)),
            Text.TextLayer(self.word, borderSize=0),
            Backgrounds.RandomDots(dotSize=2, numDots=800),
            Distortions.SineWarp(amplitudeRange=(3, 6.0)),
        ]

word = Words.defaultWordList.pick()
g = CustomTest(word=word)
i = g.render(size=(200, 50))
i.save("output.png")
word = g.solutions[0]
print word
