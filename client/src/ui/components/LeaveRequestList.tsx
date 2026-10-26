import React, { useEffect, useState } from 'react';
import { useAuth } from '../auth/AuthProvider';
import { useQuery } from 'react-query';
import { LeaveRequest } from '../api/elm';

const LeaveRequestList = () => {
    const { user } = useAuth();
    const { data, isLoading, error } = useQuery('leaveRequests', async () => {
        const response = await fetch('/api/v1/elm/leave-requests/', {
            headers: {
                'Authorization': `Bearer ${user.token}`,
            },
        });

        if (!response.ok) {
            throw new Error('Failed to fetch leave requests');
        }

        return response.json();
    });

    if (isLoading) return <div>Loading...</div>;
    if (error) return <div>Error: {error.message}</div>;

    return (
        <ul>
            {data.map((request) => (
                <li key={request.id}>
                    {request.user} - {request.start_date} to {request.end_date} - {request.reason} - {request.status}
                </li>
            ))}
        </ul>
    );
};

export default LeaveRequestList;
