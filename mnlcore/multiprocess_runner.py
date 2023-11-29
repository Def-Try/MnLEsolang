from multiprocessing import Pipe

def init_worker(engine):
	a, _ = Pipe(duplex=True)
	def mnl_worker(engine, pipe_duplex):
		while True:
			#length = int.from_bytes(pipe_duplex.recv_bytes(8), 'little')
			code = pipe_duplex.recv()
			try:
				ret = engine.run(code)
			except Exception as e:
				pipe_duplex.send([False, e])
				continue
			pipe_duplex.send([True, ret])
	p = multiprocessing.Process(target=mnl_worker, args=(engine, a))
	return p, a

def run(code, pipe):
	pipe.send(code)
	ret = pipe.recv()
	if not ret: raise ret[1]
	return ret[1]