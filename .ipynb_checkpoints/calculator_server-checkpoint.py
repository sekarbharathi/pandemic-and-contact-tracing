import grpc
from concurrent import futures
import calculator_pb2
import calculator_pb2_grpc
class CalculatorService(calculator_pb2_grpc.CalculatorServicer):
   def Add(self, request, context):
       return calculator_pb2.AddResponse(result=request.num1 + request.num2)
def serve():
   server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
   calculator_pb2_grpc.add_CalculatorServicer_to_server(CalculatorService(), server)
   server.add_insecure_port('[::]:50051')
   server.start()
   print("gRPC Server Running on Port 50051...")
   server.wait_for_termination()
if __name__ == "__main__":
   serve()