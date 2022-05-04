import { React, useState, useEffect} from 'react';
import { Box, Heading, Text, Code, Stat, StatLabel, StatNumber, StatHelpText } from '@chakra-ui/react'
import VisGraph, { GraphData, GraphEvents, Options} from 'react-vis-graph-wrapper';
import TreeViewMenu from './TreeViewMenu';

let TreeView = ({name, program, jsonTree, currNodeID, currFlaggedNodeID, cNodes, eventProps, clickHandler}) => {
	const [nodeID, setNodeID] = useState(undefined);
	const [flaggedNodeID, setFlaggedNodeID] = useState(undefined);
	const [tree, setTree] = useState(undefined);
	const [hasLoaded, setHasLoaded] = useState(false);
	const [hasSelectedNode, setHasSelectedNode] = eventProps;

	const colouriseTree = (tree, nID, fnID) => {
		console.log("n ", nID, ", f ", fnID);
		let colouredNodes = tree.nodes.map((node) => {
			if (node.id === fnID) {
				console.log(node.id === fnID)
				node.color = {
					background: "#e74c3c",
					border: "#e74c3c",
				}
			} else if (cNodes.includes(node.id)) {
				node.color = {
					background: "#58d68d",
					border: "#58d68d",
				}
			}
			return {...node}
		});
		console.log(colouredNodes);
		tree.nodes = colouredNodes;		
	}

	useEffect(() => {
		if (jsonTree) {
			colouriseTree(jsonTree, currNodeID, currFlaggedNodeID);
			setTree(jsonTree);
			setNodeID(currNodeID);
			setFlaggedNodeID(currFlaggedNodeID);
			setHasLoaded(true);
		}
	}, [jsonTree, currNodeID, currFlaggedNodeID]); 

	const options = {
		layout: {
			hierarchical: { 
				enabled: true,
				nodeSpacing: 200,
				direction: 'UD',
				sortMethod: 'directed'
			}
		},
		interaction : {
			hover : true,
		},
		nodes : {
			shape: 'box'
		},
		edges: {
		  color: '#000000',
		  arrows: {
			to: {
				enabled: true
			}
		},
		smooth: {
			enabled: false,
			type: 'continuous'
		}
		},
		height: '500px',
		physics : {
			enabled : true,
			hierarchicalRepulsion: {
				centralGravity: 0.0,
				springLength: 0,
				springConstant: 0.01,
				nodeDistance: 200,
				damping: 0.09
			},
			solver: 'hierarchicalRepulsion'
		}
	};

	const renderNodeInfo = (tree) => {
		if (tree == null) {
			return
		}
		const node = tree.nodes.find((node) => {
			if (node.id === nodeID) {
				return node
			}
			return null;
		});
		const strip = (str) => {
			if (str.charAt(0) === "{") {
				return str.substring(1);
			}
			return str
		}
		if (node != null) {
			const label = <b> {node.label} </b>
			return (
				<Stat>
					<StatLabel> Current Node </StatLabel>
					<StatNumber> {nodeID} </StatNumber>
					<StatHelpText> {label} </StatHelpText>
					<StatHelpText> 
						{node.title.split("}\n").map(pair => (
							<Text>
								{pair.split("\n").map(s => s.trim())[0] + " "}
								{<Code colorScheme="blue" variant="outline"> 
									{strip(pair.split("\n").map(s => s.trim())[1])} 
								</Code>}
							</Text>
						))} 
				</StatHelpText>
				</Stat>
			); 
		}
	}
	  
	const events = {
		select: (event) => {
			const { nodes, edges } = event;
			if (nodes.length > 0 && edges.length > 0) {
				setHasSelectedNode(true);
			} else {
				setHasSelectedNode(false);	
			}
		  	console.log(nodes, edges, hasSelectedNode);
		},
	};
	
	return (
		<Box p={5} shadow='md' borderWidth='1px' >
			<TreeViewMenu clickHandler={clickHandler}/>
			<Heading fontSize='xl'>{name}</Heading>
			<Text mt={4}>{program}</Text>
			{hasLoaded &&
				<VisGraph
					graph={tree}
					options={options}
					events={events}
					getNetwork={(network) => {console.log(network);}}
				/>
			}
			{renderNodeInfo(tree)}
	  </Box>
	)
}

export default TreeView;