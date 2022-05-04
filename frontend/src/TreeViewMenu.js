import { React, useState, useEffect } from 'react';
import { useDisclosure, Menu, MenuButton, Button } from '@chakra-ui/react'
import { CheckIcon, CloseIcon } from '@chakra-ui/icons'

let TreeViewMenu = ({clickHandler}) => {
	const { isOpen, onOpen, onClose } = useDisclosure()
	
	const handleClick = (action) => {
		clickHandler(action);
	}

	let renderMenuButtons = () => {
		const iconsList = [<CheckIcon/>, <CloseIcon/>]
		const iconMapping = ["Yes", "No"]
		return (
			iconsList.map((icon, index) => 
				<MenuButton  
					_hover={{ bg: 'gray.400' }}
					// _expanded={{ bg: 'blue.400' }}
					_focus={{ boxShadow: 'outline' }}
					margin = {1}
					as = {Button} 
					rightIcon = {icon}
					onClick = {() => handleClick(iconMapping[index])}/>
			)
		)
	}
	return (
		<div align="left">
			<Menu isOpen={isOpen}>
				{renderMenuButtons()}
			</Menu>
		</div>
	)
}

export default TreeViewMenu;