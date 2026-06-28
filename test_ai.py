from ai.embedder import embed

vector = embed("سلام، حال شما چطوره؟")

print(type(vector))
print(len(vector))
print(vector[:10])
