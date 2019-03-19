import re

def loadIWSLT17(src='en', target='de'): 
   
    ## Load sentence pairs
    trainSentencePairs = loadSet(f'data/{src}-{target}/train.tags.{src}-{target}.{src}',
                                 f'data/{src}-{target}/train.tags.{src}-{target}.{target}',
                                 '(^[^<].*)')
    devSentencePairs = loadSet(f'data/{src}-{target}/IWSLT17.TED.dev2010.{src}-{target}.{src}.xml',
                               f'data/{src}-{target}/IWSLT17.TED.dev2010.{src}-{target}.{target}.xml',
                               '^<seg id="\d+">(.*)<\/seg>')

    testSentencePairs = loadSet(f'data/{src}-{target}/IWSLT17.TED.tst2015.{src}-{target}.{src}.xml',
                                f'data/{src}-{target}/IWSLT17.TED.tst2015.{src}-{target}.{target}.xml',
                                '^<seg id="\d+">(.*)<\/seg>')
    
    ## Tokenise


def loadSet(srcFile, targetFile, pattern):
    trainSrcFile = open(srcFile, 'r')
    trainTargetFile = open(targetFile, 'r')

    p = re.compile(pattern)

    lineSrc = trainSrcFile.readline() 
    lineTarget = trainTargetFile.readline()
     
    sentencePairs = []

    while lineSrc and lineTarget:
        if p.match(lineSrc):
            sentencePairs.append((p.match(lineSrc).group(1), p.match(lineTarget).group(1)))

        lineSrc = trainSrcFile.readline() 
        lineTarget = trainTargetFile.readline()
    
    return sentencePairs


if __name__ == "__main__":
    loadIWSLT17()