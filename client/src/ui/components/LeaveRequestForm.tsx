import React, { useState } from 'react';
import { Button, TextInput } from '@mantine/core';
import { useForm } from '@mantine/hooks';
import { useAuth } from '../auth/AuthProvider';
import { useNavigate } from 'react-router-dom';

const LeaveRequestForm = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const form = useForm({
        initialValues: {
            start_date: '',
            end_date: '',
            reason: '',
        },
    });

    const onSubmit = async (values) => {
        // Assuming we have an API client for ELM
        const response = await fetch('/api/v1/elm/leave-requests/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${user.token}`,
            },
            body: JSON.stringify(values),
        });

        if (response.ok) {
            navigate('/dashboard');
        } else {
            alert('Failed to submit leave request');
        }
    };

    return (
        <form onSubmit={form.onSubmit(onSubmit)}>
            <TextInput
                label="Start Date"
                placeholder="YYYY-MM-DD"
                {...form.getInputProps('start_date')}
            />
            <TextInput
                label="End Date"
                placeholder="YYYY-MM-DD"
                {...form.getInputProps('end_date')}
            />
            <TextInput
                label="Reason"
                placeholder="Reason for leave"
                {...form.getInputProps('reason')}
            />
            <Button type="submit">Submit</Button>
        </form>
    );
};

export default LeaveRequestForm;
