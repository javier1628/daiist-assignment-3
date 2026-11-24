# Judge rubric

<!--
Write this file yourself: the rubric is your decision. evaluate.py sends the whole file to the judge model, together
with the kind of question, the question, your reference answer, the assistant's answer and the passages it retrieved.
While any line still says TODO, the judge step is skipped.

The judge returns three fields for each answer: correct (1 or 0), supported (1 or 0) and reason. The first two are the
same two you grade yourself in eval/human_labels.csv, so define them here the way you apply them there.
-->

## correct (1 or 0)

TODO: when is an answer right against the reference answer? Say what counts as the same answer, and what to do with an answer that is right but incomplete.

## supported (1 or 0)

TODO: when is every claim in the answer backed by the retrieved passages? Say how to treat a claim that is true but is not in any passage.

## Refusals

TODO: how to grade the fixed refusal ("No puedo responder a esta pregunta con los documentos disponibles. Consulte a su agente de aduanas.") for an unanswerable question, and for a question the documents do answer.

## Partial answers

TODO: how to grade an answer that covers part of the question and ends with "No cubierto por los documentos: ...".

## reason

The judge writes one or two sentences explaining both grades. Add here anything you want it to mention.
