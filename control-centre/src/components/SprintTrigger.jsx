import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Play, CheckCircle, AlertCircle } from 'lucide-react';
import { triggerSprint } from '../../api/sprint';

const SprintTrigger = () => {
  const [isTriggering, setIsTriggering] = useState(false);
  const [status, setStatus] = useState(null);
  const [message, setMessage] = useState('');

  const handleTriggerSprint = async () => {
    setIsTriggering(true);
    setStatus(null);
    setMessage('');

    try {
      const response = await triggerSprint();
      setStatus('success');
      setMessage(`Sprint triggered successfully! Run ID: ${response.run_id}`);
    } catch (error) {
      setStatus('error');
      setMessage(error.message || 'Failed to trigger sprint');
    } finally {
      setIsTriggering(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Play className="h-5 w-5" />
          One-Click Sprint Trigger
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Trigger a new sprint execution with a single click. This will initiate
            the sprint workflow and auto-review process.
          </p>

          <Button
            onClick={handleTriggerSprint}
            disabled={isTriggering}
            className="w-full"
            size="lg"
          >
            {isTriggering ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Triggering Sprint...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Trigger Sprint
              </>
            )}
          </Button>

          {status && (
            <Alert variant={status === 'success' ? 'default' : 'destructive'}>
              {status === 'success' ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default SprintTrigger;