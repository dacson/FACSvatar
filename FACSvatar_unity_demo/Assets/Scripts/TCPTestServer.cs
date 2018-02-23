using System;
using System.Collections; 
using System.Collections.Generic; 
using System.Net; 
using System.Net.Sockets; 
using System.Text; 
using System.Threading; 
using UnityEngine;
using Newtonsoft.Json.Linq;

// TCP code: https://gist.github.com/danielbierwirth/0636650b005834204cb19ef5ae6ccedb
// JSON Unity: https://github.com/tawnkramer/sdsandbox/tree/master &
// https://assetstore.unity.com/packages/tools/input-management/json-object-710 &
// https://github.com/mtschoen/JSONObject

// Debug.Log verrrryy slow, don't use in production (>100x slower)

public class TCPTestServer : MonoBehaviour {  	
	#region private members 	
	/// <summary> 	
	/// TCPListener to listen for incomming TCP connection 	
	/// requests. 	
	/// </summary> 	
	private TcpListener tcpListener; 
	/// <summary> 
	/// Background thread for TcpServer workload. 	
	/// </summary> 	
	private Thread tcpListenerThread;  	
	/// <summary> 	
	/// Create handle to connected tcp client. 	
	/// </summary> 	
	private TcpClient connectedTcpClient; 	
	#endregion

	int counter = 0;
	//var clientMessage_json = new JObject();

	Boolean listen = false;

	// Facial expressions: Assign by dragging the GameObject with FACSnimator into the inspector before running the game.
	public FACSnimator FACSModel;

	// Head rotations: Assign by dragging the GameObject with HeadAnimator into the inspector before running the game.
	public HeadRotator RiggedModel;

		
	// Use this for initialization
	void Start () { 		
		// Start TcpServer background thread; only if model attached (preventing double start)
		if (FACSModel) {
			listen = true;
			tcpListenerThread = new Thread (new ThreadStart (ListenForIncommingRequests)); 		
			tcpListenerThread.IsBackground = true; 		
			tcpListenerThread.Start ();
		} else {
			Debug.Log (FACSModel);
			listen = false;
		}
	}

	void OnApplicationQuit() {
		listen = false;
		//tcpListener.Stop();
	}

	/*
	// Update is called once per frame
	void Update () { 		
		if (Input.GetKeyDown(KeyCode.Space)) {             
			SendMessage();         
		} 	
	}
	*/
	
	/// <summary> 	
	/// Runs in background TcpServerThread; Handles incomming TcpClient requests 	
	/// </summary> 	
	private void ListenForIncommingRequests () { 		
		try { 			
			// Create listener on localhost port 8052. 			
			tcpListener = new TcpListener(IPAddress.Parse("127.0.0.1"), 8052); 			
			tcpListener.Start();              
			Debug.Log("Server is listening");              
			Byte[] bytes = new Byte[4096];  // make sure this is big enough for JSON data		

			while (listen==true) { 				
				using (connectedTcpClient = tcpListener.AcceptTcpClient()) { 					
					// Get a stream object for reading 					
					using (NetworkStream stream = connectedTcpClient.GetStream()) { 						
						int length; 						
						// Read incomming stream into byte arrary. 						
						while ((length = stream.Read(bytes, 0, bytes.Length)) != 0) { 							
							var incommingData = new byte[length]; 							
							Array.Copy(bytes, 0, incommingData, 0, length);  							
							// Convert byte array to JSON message. 							
							String clientMessage = Encoding.UTF8.GetString(incommingData);
							//Debug.Log(clientMessage);
							// Added: convert string to JSON
							//JSONObject clientMessage_json = new JSONObject(clientMessage);
							JObject clientMessage_json = JObject.Parse(clientMessage);
							//Debug.Log("client message received as: " + clientMessage_json);

							// change the blendshapes in the main thread (put in queue used in main thread)
							// RequestBlendshapes(clientMessage_json);
							// UnityMainThreadDispatcher.Instance().Enqueue(FACSModel.RequestBlendshapes(clientMessage_json));
							JSON_splitter(clientMessage_json);

							// Tell the python client we received the message
							SendMessage ();
						} 					
					} 				
				}
			}
			// does this do something?
			tcpListener.Stop();
		} 		
		catch (SocketException socketException) { 			
			Debug.Log("SocketException " + socketException.ToString());
			//tcpListener.Stop();
		}     
	}

	private void JSON_splitter(JObject messJson) {
		// get head pose data and send to main tread
		JObject head_pose = messJson["data"]["head_pose"].ToObject<JObject>();
		UnityMainThreadDispatcher.Instance().Enqueue(RiggedModel.RequestHeadRotation(head_pose));

		// get Blend Shape dict
		JObject blend_shapes = messJson["data"]["blend_shape"].ToObject<JObject>();
		UnityMainThreadDispatcher.Instance().Enqueue(FACSModel.RequestBlendshapes(blend_shapes));
	}
		
	/// <summary> 	
	/// Send message to client using socket connection. 	
	/// </summary> 	
	private void SendMessage() { 		
		if (connectedTcpClient == null) {             
			return;         
		}  		
		
		try {
			var serverMessage = new JObject();
			// Get a stream object for writing. 			
			NetworkStream stream = connectedTcpClient.GetStream(); 			
			if (stream.CanWrite) {
				// Added: create dict to be a JSON object
				//Dictionary<string, string> serverMessage = new Dictionary<string, string>();
				//serverMessage["unity"] = String.Format("Unity sends its regards {0}", counter);
				serverMessage.Add("unity", String.Format("Unity sends its regards {0}", counter));
				counter++;

				//JSONObject serverMessage_json = new JSONObject(serverMessage);
				//String serverMessage_string = serverMessage_json.ToString();
				String serverMessage_string = serverMessage.ToString();
				//string serverMessage = "This is a message from your server.";  // original code			
				// Convert string message to byte array.                 
				byte[] serverMessageAsByteArray = Encoding.UTF8.GetBytes(serverMessage_string);  // serverMessage				
				// Write byte array to socketConnection stream.               
				stream.Write(serverMessageAsByteArray, 0, serverMessageAsByteArray.Length);               
				//Debug.Log("Server sent his message - should be received by client");           
			}       
		} 		
		catch (SocketException socketException) {             
			Debug.Log("Socket exception: " + socketException);         
		} 	
	} 
}