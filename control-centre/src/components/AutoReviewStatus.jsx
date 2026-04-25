import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, GitPullRequest, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { fetchPRReviews } from '../../api/reviews';

const AutoReviewStatus = () => {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadReviews();
    const interval = setInterval(loadReviews, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadReviews = async () => {
    try {
      const data = await fetchPRReviews();
      setReviews(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'changes_requested':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      approved: 'default',
      changes_requested: 'destructive',
      pending: 'secondary',
    };
    return (
      <Badge variant={variants[status] || 'outline'}>
        {status.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center p-6">
          <Loader2 className="h-6 w-6 animate-spin" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GitPullRequest className="h-5 w-5" />
          Auto Review Status
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="text-sm text-red-500">Error: {error}</div>
        ) : reviews.length === 0 ? (
          <div className="text-sm text-muted-foreground">No PRs with reviews</div>
        ) : (
          <ScrollArea className="h-[400px] pr-4">
            <div className="space-y-3">
              {reviews.map((review) => (
                <div
                  key={review.pr_id}
                  className="border rounded-lg p-3 hover:bg-accent transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        {getStatusIcon(review.status)}
                        <span className="font-medium text-sm truncate">
                          #{review.pr_number} {review.title}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground mb-2">
                        {review.author} • {new Date(review.created_at).toLocaleDateString()}
                      </div>
                      {review.review_summary && (
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {review.review_summary}
                        </p>
                      )}
                    </div>
                    {getStatusBadge(review.status)}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
};

export default AutoReviewStatus;