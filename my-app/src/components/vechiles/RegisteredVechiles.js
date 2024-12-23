// src/components/RegisteredVehicles.js
import React, { useEffect, useState } from 'react';
import { Grid2, TextField, Button, Table, TableHead, TableRow, TableCell, TableBody, Container } from '@mui/material';
import { addVechile, getVechiles } from './registererdVechilesApi';

const RegisteredVehicles = () => {
  const [vehicles, setVehicles] = useState([
  //   { number: 'PB01A4470', owner: 'Harpreet Singh', model: 'Toyota Innova', year: 2024 },
  //   { number: 'PB11V0012', owner: 'Ankit Gupta', model: 'Honda City', year: 2024 },
  //   { number: 'CH02AA8347', owner: 'Jaspal Singh', model: 'Toyota Fortuner', year: 2024 },
  //   { number: 'HP02Z1086', owner: 'Himanshu Bansal', model: 'Maruti Alto 800', year: 2024 },
   ]
);

  const [newVehicle, setNewVehicle] = useState({ number: '', owner: '', model: '', year: '' });
  const [showForm, setShowForm] = useState(false);

  const handleInputChange = (e) => setNewVehicle({ ...newVehicle, [e.target.name]: e.target.value });
  const handleFormSubmit = (e) => {
    e.preventDefault();
    setVehicles([...vehicles, newVehicle]);
    setNewVehicle({ number: '', owner: '', model: '', year: '' });
    addVechile(newVehicle);
    setShowForm(false);
  };

 //use the api created to fetch the data
  useEffect(() => {
    getVechiles().then(response =>
      setVehicles(response)
    );
  },[]);

  return (
    <Container maxWidth="lg" sx={{ mt: 4 ,textAlign: 'center' }}>
      <h1>Registered Vehicles</h1>
      <Button variant="contained" onClick={() => setShowForm(!showForm)} sx={{ mt: 2,mb:2 }}>
        {showForm ? 'Cancel' : 'Register New Vehicle'}
      </Button>

      {showForm && (
        <form onSubmit={handleFormSubmit}>
          <Grid2 container spacing={2} sx={{ my: 2 }}>
            <Grid2 size={{xs:12,sm:6}}>
              <TextField label="Vehicle Number" name="number" value={newVehicle.number} onChange={handleInputChange} required fullWidth />
            </Grid2>
            <Grid2 size={{xs:12,sm:6}} >
              <TextField label="Owner" name="owner" value={newVehicle.owner} onChange={handleInputChange} required fullWidth />
            </Grid2>
            <Grid2 size={{xs:12,sm:6}} >
              <TextField label="Model" name="model" value={newVehicle.model} onChange={handleInputChange} required fullWidth />
            </Grid2>
            <Grid2 size={{xs:12,sm:6}} >
              <TextField label="Year" name="year" value={newVehicle.year} onChange={handleInputChange} required type="number" fullWidth />
            </Grid2>
          </Grid2>
          <Button type="submit" variant="contained" color="primary">Add Vehicle</Button>
        </form>
      )}
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Vehicle Number</TableCell>
            <TableCell>Owner</TableCell>
            <TableCell>Model</TableCell>
            <TableCell>Year</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {vehicles && vehicles.map((vehicle, index) => (
            <TableRow key={index}>
              <TableCell>{vehicle.number}</TableCell>
              <TableCell>{vehicle.owner}</TableCell>
              <TableCell>{vehicle.model}</TableCell>
              <TableCell>{vehicle.year}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      

      
    </Container>
  );
};

export default RegisteredVehicles;
