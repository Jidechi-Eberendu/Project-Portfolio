
import { Property } from "@/types/property";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useState } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";

interface PropertyTableProps {
  properties: Property[];
  showLimited?: boolean;
}

type SortField = 'address' | 'price' | 'bedrooms' | 'type' | 'timeOnMarket' | 'aiScore';
type SortDirection = 'asc' | 'desc';

export const PropertyTable = ({ properties, showLimited = false }: PropertyTableProps) => {
  const [sortField, setSortField] = useState<SortField>('price');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedProperties = [...properties].sort((a, b) => {
    let aValue: any = a[sortField];
    let bValue: any = b[sortField];

    // Handle null values
    if (aValue === null) aValue = '';
    if (bValue === null) bValue = '';

    // Convert to numbers for numeric fields
    if (sortField === 'price' || sortField === 'bedrooms' || sortField === 'aiScore') {
      aValue = Number(aValue);
      bValue = Number(bValue);
    }

    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  const displayedProperties = showLimited ? sortedProperties.slice(0, 6) : sortedProperties;

  const exportToCSV = () => {
    if (sortedProperties.length === 0) {
      toast.error("No properties to export");
      return;
    }

    // Create properly formatted CSV headers with extra spacing
    const headers = [
      "Property Address",
      "Price (£)",
      "Number of Bedrooms",
      "Property Type",
      "Time on Market",
      "AI Investment Score"
    ];
    
    // Create CSV rows with proper formatting and spacing
    const csvData = sortedProperties.map(property => [
      `"${property.address}"`,
      `"£${property.price.toLocaleString()}"`,
      `"${property.bedrooms} bed${property.bedrooms !== 1 ? 's' : ''}"`,
      `"${property.type || 'Not specified'}"`,
      `"${property.timeOnMarket || 'Not available'}"`,
      `"${property.aiScore}/10"`
    ]);

    // Combine headers and data with proper CSV formatting
    const csvContent = [
      headers.join(','),
      ...csvData.map(row => row.join(','))
    ].join('\r\n');

    // Add BOM for proper Excel encoding
    const BOM = '\uFEFF';
    const csvWithBOM = BOM + csvContent;

    // Create and download file
    const blob = new Blob([csvWithBOM], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `property_listings_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    toast.success("Properties exported to CSV successfully!");
  };

  const SortButton = ({ field, children }: { field: SortField; children: React.ReactNode }) => (
    <button
      onClick={() => handleSort(field)}
      className="flex items-center gap-1 hover:text-gray-700 transition-colors"
    >
      {children}
      {sortField === field && (
        sortDirection === 'asc' ? 
        <ChevronUp className="h-4 w-4" /> : 
        <ChevronDown className="h-4 w-4" />
      )}
    </button>
  );

  return (
    <div className="w-full max-w-4xl mx-auto mt-8 p-6 bg-white rounded-lg shadow-sm animate-fadeIn">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">
          Property List {showLimited && `(Showing ${displayedProperties.length} of ${properties.length})`}
        </h2>
        <Button 
          variant="outline"
          className="hover:bg-gray-50 transition-colors"
          onClick={exportToCSV}
        >
          Export to CSV
        </Button>
      </div>
      
      {showLimited && properties.length > 6 && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <p className="text-sm text-blue-800">
            Showing first {displayedProperties.length} properties. Export to CSV to see all {properties.length} listings.
          </p>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                <SortButton field="address">Address</SortButton>
              </th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                <SortButton field="price">Price</SortButton>
              </th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                <SortButton field="bedrooms">Bedrooms</SortButton>
              </th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                <SortButton field="type">Type</SortButton>
              </th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                <SortButton field="timeOnMarket">Time on Market</SortButton>
              </th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                <SortButton field="aiScore">AI Score</SortButton>
              </th>
            </tr>
          </thead>
          <tbody>
            {displayedProperties.map((property, index) => (
              <motion.tr
                key={property.address}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className="border-b hover:bg-gray-50 transition-colors"
              >
                <td className="py-3 px-4 text-sm text-gray-900">{property.address}</td>
                <td className="py-3 px-4 text-sm text-gray-900">£{property.price.toLocaleString()}</td>
                <td className="py-3 px-4 text-sm text-gray-900">{property.bedrooms}</td>
                <td className="py-3 px-4 text-sm text-gray-900">{property.type || "Not specified"}</td>
                <td className="py-3 px-4 text-sm text-gray-900">{property.timeOnMarket || "Not available"}</td>
                <td className="py-3 px-4 text-sm text-gray-900">{property.aiScore}/10</td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
