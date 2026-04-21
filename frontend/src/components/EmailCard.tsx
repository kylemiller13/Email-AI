import {
  Box,
  VStack,
  HStack,
  Text,
  Badge,
  Progress,
  Button,
} from '@chakra-ui/react';

interface EmailCardProps {
  email: {
    id: string;
    subject: string;
    from: string;
    risk_score: number;
    risk_level: string;
    indicators: string[];
    timestamp: string;
  };
  onClick: () => void;
}

const EmailCard = ({ email, onClick }: EmailCardProps) => {
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'semantic.critical';
      case 'warning':
        return 'semantic.warning';
      case 'caution':
        return 'semantic.caution';
      case 'safe':
        return 'semantic.safe';
      default:
        return 'gray.500';
    }
  };

  const getRiskBadgeColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'red';
      case 'warning':
        return 'orange';
      case 'caution':
        return 'yellow';
      case 'safe':
        return 'green';
      default:
        return 'gray';
    }
  };

  return (
    <Box
      bg="gray.800"
      rounded="lg"
      p={6}
      border="1px"
      borderColor="gray.700"
      _hover={{
        borderColor: 'brand.500',
        boxShadow: '0 0 20px rgba(59, 130, 246, 0.1)',
        transform: 'translateY(-2px)',
        transition: 'all 0.2s',
      }}
      cursor="pointer"
      onClick={onClick}
    >
      <VStack align="start" spacing={4}>
        {/* Header */}
        <HStack justify="space-between" w="full">
          <VStack align="start" spacing={1} flex={1}>
            <Text fontSize="sm" color="gray.400" noOfLines={1}>
              From: {email.from}
            </Text>
            <Text fontSize="sm" fontWeight="600" noOfLines={2}>
              {email.subject}
            </Text>
          </VStack>
          <Badge
            colorScheme={getRiskBadgeColor(email.risk_level)}
            textTransform="capitalize"
            px={3}
            py={1}
            rounded="full"
          >
            {email.risk_level}
          </Badge>
        </HStack>

        {/* Risk Score */}
        <VStack w="full" spacing={2} align="start">
          <HStack justify="space-between" w="full">
            <Text fontSize="xs" color="gray.400" fontWeight="600">
              Risk Score
            </Text>
            <Text fontSize="sm" fontWeight="bold" color={getRiskColor(email.risk_level)}>
              {Math.round(email.risk_score * 100)}%
            </Text>
          </HStack>
          <Progress
            value={email.risk_score * 100}
            size="sm"
            rounded="full"
            colorScheme={getRiskBadgeColor(email.risk_level)}
            w="full"
          />
        </VStack>

        {/* Indicators */}
        {email.indicators.length > 0 && (
          <VStack align="start" w="full" spacing={2}>
            <Text fontSize="xs" color="gray.400" fontWeight="600">
              Risk Indicators ({email.indicators.length})
            </Text>
            <HStack spacing={2} flexWrap="wrap">
              {email.indicators.slice(0, 3).map((indicator, idx) => (
                <Badge key={idx} variant="subtle" colorScheme="orange" fontSize="xs">
                  {indicator}
                </Badge>
              ))}
              {email.indicators.length > 3 && (
                <Text fontSize="xs" color="gray.500">
                  +{email.indicators.length - 3} more
                </Text>
              )}
            </HStack>
          </VStack>
        )}

        {/* Timestamp */}
        <Text fontSize="xs" color="gray.500">
          {new Date(email.timestamp).toLocaleDateString()}
        </Text>

        {/* View Details Button */}
        <Button
          size="sm"
          colorScheme="brand"
          variant="ghost"
          w="full"
          mt={2}
          onClick={(e) => {
            e.stopPropagation();
            onClick();
          }}
        >
          View Details
        </Button>
      </VStack>
    </Box>
  );
};

export default EmailCard;
