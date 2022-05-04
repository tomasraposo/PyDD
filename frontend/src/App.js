import { React, useRef, useState, useEffect } from 'react';
import { ChakraProvider, Spinner, Box, Text, theme, Stack, Heading, Alert, AlertIcon, AlertDescription, } from '@chakra-ui/react';
import { ColorModeSwitcher } from './ColorModeSwitcher';
import TreeView from "./TreeView";

let App = () => {
  const [file, setFile] = useState(undefined);
  const [execTree, setExecTree] = useState(undefined);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [hasSelectedNode, setHasSelectedNode] = useState(false);
  const [cmdOutput, setCmdOutput] = useState([]);
  const [nodeID, setNodeID] = useState(-1);
  const [flaggedNodeID, setFlaggedNodeID] = useState(-1);
  const [correctNodes, setCorrectNodes] = useState([]);
  const [foundBug, setFoundBug] = useState([false, ""]);
  
  const websocket = useRef(null);

  const send = (message) => {
    if (message === "Yes") {
      setCorrectNodes(cNodes => [...cNodes, nodeID]);
    } else if (message === "No") {
      setFlaggedNodeID(nodeID);
    }
    if (websocket.current.readyState === WebSocket.OPEN) {
        console.log("sending ... ", message);
        websocket.current.send(JSON.stringify(message))
    }
    console.log("\ncurrNode: ", nodeID, 
                "\nflaggedNodes: ",flaggedNodeID, 
                "\ncorrectNodes: ", correctNodes);
  }

  useEffect(() => {
    websocket.current = new WebSocket("ws://localhost:8001/");
    websocket.current.onopen = () => console.log("websocket opened");
    websocket.current.onclose = () => console.log("websocket closed"); 
  }, []); // on App mount

  useEffect(() => {
      return () => websocket.current.close();
  }, []); // on App unmount:
  
  useEffect(() => {
      if (!websocket.current) return;
      websocket.current.onmessage = (e) => {
        try {
          const message = JSON.parse(e.data);
          console.log(message);
          const type = message.type
          if (type === "tree") {
            const file = ""
            const tree = message.tree
            setExecTree(tree);
            setFile(file);
            setHasLoaded(true)
          } else if (type === "cmd") {
            const output = message.cmd.output
            setCmdOutput(output)
          } else if (type === "id") {
            const id = message.id
            setNodeID(id); 
         } 
      } catch (err) {
          let message = e.data;
          setFoundBug([true, message]);
          setFlaggedNodeID(nodeID);
        }
    };
  }, [execTree, file, cmdOutput, nodeID, flaggedNodeID]);

    let [isDone, alertMessage] = foundBug;
    return (
      <ChakraProvider theme={theme}>
        <ColorModeSwitcher justifySelf="flex-end" />
        <Box textAlign="center" fontSize="xl" direction = "flex">
        {hasLoaded ? 
          <>
            <Heading> PyDD </Heading>
            <Text color='gray.500'> {file} </Text>
              <Stack 
                h="100%"
                justifyContent="center"
                transition="0.8s linear" 
                direction={['column']} 
                spacing='24px'
                padding='12px'>
                {isDone && 
                  <Box maxW='md'>
                    <Alert status='error'>
                      <AlertIcon/>
                      <AlertDescription> {alertMessage} </AlertDescription>
                    </Alert>
                  </Box>
                }
                <TreeView 
                  name = "Execution Tree"
                  program = {file}
                  jsonTree = {execTree}
                  currNodeID = {nodeID}
                  currFlaggedNodeID = {flaggedNodeID}
                  cNodes = {correctNodes}
                  eventProps = {[hasSelectedNode, setHasSelectedNode]} 
                  clickHandler = {send}/>
                  </Stack>
          </>
          : <Spinner/>
        }
      </Box>
    </ChakraProvider>
  );
}

export default App;
